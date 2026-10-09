#!/usr/bin/env python3
"""Scan a SQL file (e.g. a database dump) for words from a word list.

The word list is a text file with one word per line. Empty lines and
lines starting with '#' are ignored. Matching is case-insensitive and
only matches whole words.

Exit code is 0 when no words are found, 1 when matches are found,
and 2 on input errors (useful in CI pipelines).

Usage:
    python sql_profanity_checker.py dump.sql --words examples/profanity_words.txt
"""

import argparse
import re
import sys
from typing import Dict, List, Optional


def load_word_list(filepath: str, encoding: str = "utf-8") -> List[str]:
    """Load words from a text file, one per line. Falls back to latin-1 if decoding fails."""
    try:
        with open(filepath, "r", encoding=encoding) as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print(f"WARNING: could not decode '{filepath}' as {encoding}, trying latin-1.", file=sys.stderr)
        with open(filepath, "r", encoding="latin-1") as f:
            lines = f.readlines()

    words = []
    for line in lines:
        word = line.strip()
        if word and not word.startswith("#"):
            words.append(word.lower())
    return words


def find_words(sql_path: str, words: List[str], encoding: str = "utf-8") -> Optional[Dict]:
    """Search sql_path for any word in `words`. Returns a report dict, or None if nothing matched."""
    if not words:
        raise ValueError("the word list is empty")

    try:
        with open(sql_path, "r", encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"WARNING: could not decode '{sql_path}' as {encoding}, trying latin-1.", file=sys.stderr)
        with open(sql_path, "r", encoding="latin-1") as f:
            content = f.read()

    # \b keeps matches to whole words; re.escape handles special characters in the list
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE)

    matches = pattern.findall(content)
    if not matches:
        return None

    report = {
        "found_words": sorted({m.lower() for m in matches}),
        "total_count": len(matches),
        "details": {},
    }

    for line_num, line in enumerate(content.splitlines(), 1):
        for match in pattern.findall(line):
            report["details"].setdefault(match.lower(), set()).add(line_num)

    report["details"] = {word: sorted(lines) for word, lines in report["details"].items()}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find words from a word list inside a SQL file.")
    parser.add_argument("sql_file", help="SQL file to scan")
    parser.add_argument("-w", "--words", required=True, help="text file with one word per line")
    parser.add_argument("--encoding", default="utf-8", help="encoding for both files (default: utf-8)")
    args = parser.parse_args(argv)

    print(f"Loading word list from: {args.words}")
    try:
        words = load_word_list(args.words, args.encoding)
    except OSError as e:
        print(f"ERROR: cannot read word list: {e}", file=sys.stderr)
        return 2

    if not words:
        print("ERROR: the word list is empty.", file=sys.stderr)
        return 2
    print(f"Loaded {len(words)} words.")

    print(f"\nScanning SQL file: {args.sql_file}")
    try:
        report = find_words(args.sql_file, words, args.encoding)
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if report is None:
        print("\nNo matches found.")
        return 0

    print("\n*** MATCHES FOUND ***")
    print(f"Words found ({report['total_count']} matches): {', '.join(report['found_words'])}")
    print("\nDetails by word and line:")
    for word, lines in report["details"].items():
        print(f"- '{word.upper()}': lines {', '.join(map(str, lines))}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
