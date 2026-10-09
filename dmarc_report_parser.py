#!/usr/bin/env python3
"""Summarize DMARC aggregate reports (XML files) from a folder.

Usage:
    python dmarc_report_parser.py path/to/reports
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone


def safe_find_text(parent, path):
    if parent is None:
        return None
    el = parent.find(path)
    return el.text.strip() if el is not None and el.text else None


def parse_dmarc_xml(xml_path):
    """Parse one DMARC aggregate report. Returns a dict, or None if invalid."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        meta = root.find(".//report_metadata")
        policy = root.find(".//policy_published")

        if meta is None or policy is None:
            print(f"WARNING: invalid or incomplete report: {xml_path}")
            return None

        begin = int(safe_find_text(meta, "date_range/begin") or 0)
        end = int(safe_find_text(meta, "date_range/end") or 0)

        report = {
            "file": os.path.basename(xml_path),
            "org": safe_find_text(meta, "org_name"),
            "report_id": safe_find_text(meta, "report_id"),
            "date_begin": datetime.fromtimestamp(begin, tz=timezone.utc) if begin else None,
            "date_end": datetime.fromtimestamp(end, tz=timezone.utc) if end else None,
            "domain": safe_find_text(policy, "domain"),
            "aspf": safe_find_text(policy, "aspf"),
            "adkim": safe_find_text(policy, "adkim"),
            "policy": safe_find_text(policy, "p"),
            "records": [],
        }

        for rec in root.findall(".//record"):
            row = rec.find("row")
            identifiers = rec.find("identifiers")
            auth = rec.find("auth_results")

            if row is None:
                continue

            policy_eval = row.find("policy_evaluated")
            dkim = auth.find("dkim") if auth is not None else None
            spf = auth.find("spf") if auth is not None else None

            record = {
                "ip": safe_find_text(row, "source_ip"),
                "count": int(safe_find_text(row, "count") or 0),
                "disposition": safe_find_text(policy_eval, "disposition") or "none",
                "dkim_policy": safe_find_text(policy_eval, "dkim"),
                "spf_policy": safe_find_text(policy_eval, "spf"),
                "header_from": safe_find_text(identifiers, "header_from") if identifiers is not None else None,
                "envelope_from": safe_find_text(identifiers, "envelope_from") if identifiers is not None else None,
                "dkim_domain": safe_find_text(dkim, "domain") if dkim is not None else None,
                "dkim_result": safe_find_text(dkim, "result") if dkim is not None else None,
                "spf_domain": safe_find_text(spf, "domain") if spf is not None else None,
                "spf_result": safe_find_text(spf, "result") if spf is not None else None,
            }
            report["records"].append(record)

        return report

    except Exception as e:
        print(f"ERROR parsing {xml_path}: {e}")
        return None


def is_spf_aligned(spf_domain, header_from):
    """SPF is aligned when the envelope domain equals the From domain or is a subdomain of it."""
    return spf_domain == header_from or spf_domain.endswith("." + header_from)


def analyze_reports(reports_dir):
    domain_summary = defaultdict(int)
    ip_summary = defaultdict(int)
    inbox = spam = rejected = 0

    print(f"\nAnalyzing folder: {reports_dir}\n")

    for file in sorted(os.listdir(reports_dir)):
        if not file.lower().endswith(".xml"):
            continue

        report = parse_dmarc_xml(os.path.join(reports_dir, file))
        if not report:
            continue

        print(f"\n=== Report: {report['file']} ===")
        print(f"Org: {report['org']}")
        print(f"Domain: {report['domain']}")
        print(f"Period: {report['date_begin']} -> {report['date_end']}")
        print(f"Policy: {report['policy']} (aspf={report['aspf']}, adkim={report['adkim']})\n")

        for r in report["records"]:
            domain_summary[report["domain"]] += r["count"]
            ip_summary[r["ip"]] += r["count"]

            if r["disposition"] == "none":
                inbox += r["count"]
            elif r["disposition"] == "quarantine":
                spam += r["count"]
            elif r["disposition"] == "reject":
                rejected += r["count"]

            dkim_pass = r["dkim_policy"] == "pass"
            spf_pass = r["spf_policy"] == "pass"

            print(f"IP: {r['ip']} ({r['count']} emails)")
            print(f"  From: {r['header_from']}")
            print(f"  Envelope: {r['envelope_from']}")
            print(f"  SPF: {r['spf_result']} -> DMARC: {'pass' if spf_pass else 'fail'}")
            print(f"  DKIM: {r['dkim_result']} -> DMARC: {'pass' if dkim_pass else 'fail'}")

            if r["spf_result"] == "pass" and r["header_from"] and r["spf_domain"]:
                if not is_spf_aligned(r["spf_domain"], r["header_from"]):
                    print("  WARNING: SPF alignment FAIL (external domain)")

            print()

    print("\n==============================")
    print("SUMMARY BY DOMAIN")
    print("==============================")
    for d, count in domain_summary.items():
        print(f"{d}: {count} emails")

    print("\n==============================")
    print("SUMMARY BY IP")
    print("==============================")
    for ip, count in sorted(ip_summary.items(), key=lambda x: x[1], reverse=True):
        print(f"{ip}: {count} emails")

    print("\n==============================")
    print("DELIVERY")
    print("==============================")
    print(f"Inbox (approx): {inbox}")
    print(f"Spam: {spam}")
    print(f"Rejected: {rejected}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize DMARC aggregate XML reports.")
    parser.add_argument(
        "reports_dir",
        nargs="?",
        default="./dmarc_reports",
        help="folder containing the .xml report files (default: ./dmarc_reports)",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.reports_dir):
        print(f"ERROR: folder not found: {args.reports_dir}", file=sys.stderr)
        return 1

    analyze_reports(args.reports_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
