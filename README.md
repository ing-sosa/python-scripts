# Python Scripts

A small collection of standalone Python command-line tools. Each script is a single file, takes its inputs as arguments, and has no configuration to edit.

| Script | What it does | Extra dependency |
| --- | --- | --- |
| [`dmarc_report_parser.py`](#dmarc_report_parserpy) | Summarizes DMARC aggregate XML reports | none |
| [`image_optimizer.py`](#image_optimizerpy) | Resizes and compresses images for the web | Pillow |
| [`sql_profanity_checker.py`](#sql_profanity_checkerpy) | Finds words from a word list inside a SQL file | none |

## Setup

Requires Python 3.8 or newer.

```bash
git clone https://github.com/ing-sosa/python-scripts.git
cd python-scripts
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt                      # only needed for image_optimizer.py
```

Run any script with `--help` to see all options.

---

## dmarc_report_parser.py

Reads every `.xml` file in a folder (DMARC aggregate reports sent by mail providers) and prints:

- per-report details: organization, domain, period, policy
- per-source-IP results: SPF and DKIM outcome, DMARC pass/fail, alignment warnings
- totals by domain, by IP, and by delivery outcome (inbox, quarantine, rejected)

```bash
python dmarc_report_parser.py ./dmarc_reports
```

If no folder is given, it uses `./dmarc_reports`.

## image_optimizer.py

Processes every image (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`) in a folder:

- scales it down to a maximum width, keeping the aspect ratio (never enlarges)
- sets the DPI metadata
- saves JPEG with the chosen quality and optimized PNG

```bash
python image_optimizer.py ./originals ./optimized
python image_optimizer.py ./originals ./optimized --max-width 800 --dpi 96 --quality 80
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--max-width` | `500` | maximum width in pixels |
| `--dpi` | `72` | DPI metadata written to each file |
| `--quality` | `85` | JPEG quality (1–95) |

Notes: animated GIFs are saved as a single frame, and the output folder is created if it does not exist.

## sql_profanity_checker.py

Scans a SQL file (for example a database dump) for whole words from a word list, ignoring case. It reports each word found and the line numbers where it appears.

```bash
python sql_profanity_checker.py dump.sql --words examples/profanity_words.txt
```

The word list is a plain text file with one word per line. Lines starting with `#` and empty lines are ignored. The tool works with any language; `examples/profanity_words.txt` is only a placeholder.

Exit codes: `0` no matches, `1` matches found, `2` input error. This makes it usable in CI.

---

## License

[MIT](LICENSE)
