import argparse
import json
import sys
from datetime import datetime

from services.email_parser import parse_email, ParsedEmail
from services.email_thread import extract_thread, ThreadEmail
from services.extraction import _rule_based_fallback


_COLOR_GREEN = "\033[92m"
_COLOR_YELLOW = "\033[93m"
_COLOR_RED = "\033[91m"
_COLOR_GREY = "\033[90m"
_COLOR_RESET = "\033[0m"
_COLOR_CYAN = "\033[96m"
_COLOR_BOLD = "\033[1m"


def _color_availability(status: str) -> str:
    colors = {
        "green": _COLOR_GREEN,
        "yellow": _COLOR_YELLOW,
        "red": _COLOR_RED,
        "grey": _COLOR_GREY,
        "black": _COLOR_GREY,
    }
    c = colors.get(status, "")
    return f"{c}{status.upper():<8}{_COLOR_RESET}"


def print_parsed(parsed: ParsedEmail, use_color: bool = True) -> None:
    print(f"\n{_COLOR_BOLD}Subject:{_COLOR_RESET} {parsed.subject}")
    print(f"{_COLOR_BOLD}From:{_COLOR_RESET} {parsed.sender}")
    print(f"{_COLOR_BOLD}Date:{_COLOR_RESET} {parsed.date}")
    print(f"{_COLOR_BOLD}Recipients:{_COLOR_RESET} {parsed.recipients}")
    print(f"{_COLOR_BOLD}Rows:{_COLOR_RESET} {len(parsed.rows)}\n")

    if not parsed.rows:
        print("No table rows found in email.")
        return

    header = f"{'Division':<15} {'Brand/Category':<25} {'Status':<10} {'Milestone':<35} {'Comments'}"
    print(header)
    print("-" * len(header))

    for row in parsed.rows:
        avail = _color_availability(row.availability) if use_color else row.availability.upper().ljust(8)
        milestone = row.milestone[:34] + "..." if len(row.milestone) > 34 else row.milestone
        comments = row.comments[:50] + "..." if len(row.comments) > 50 else row.comments
        print(f"{row.division:<15} {row.brand_category:<25} {avail} {milestone:<35} {comments}")

        if row.milestone_ar or row.comments_ar:
            if row.milestone_ar:
                print(f"{'':<15} {'':<25} {'':<10} {_COLOR_CYAN}[AR]{_COLOR_RESET} {row.milestone_ar[:60]}")
            if row.comments_ar:
                print(f"{'':<15} {'':<25} {'':<10} {_COLOR_CYAN}[AR]{_COLOR_RESET} {row.comments_ar[:60]}")

    print()


def print_extraction(parsed: ParsedEmail) -> None:
    result = _rule_based_fallback(parsed)
    print(f"\n{_COLOR_BOLD}Extraction Results:{_COLOR_RESET}")
    print(f"  Items: {len(result.items)}")
    print(f"  Tasks: {len(result.tasks)}")
    print(f"  Insights: {len(result.insights)}\n")

    if result.items:
        print(json.dumps(result.items, indent=2, ensure_ascii=False))


def print_thread_email(email: ThreadEmail, index: int, total: int, use_color: bool) -> None:
    date_label = email.date.strftime("%Y-%m-%d %H:%M") if email.date else email.date_str[:20]
    print(f"\n{_COLOR_BOLD}{'='*60}{_COLOR_RESET}")
    print(f"{_COLOR_BOLD}[{index}/{total}] Email from {date_label}{_COLOR_RESET}")
    print(f"{_COLOR_BOLD}  From:{_COLOR_RESET} {email.sender[:60]}")
    print(f"{_COLOR_BOLD}  Subject:{_COLOR_RESET} {email.subject[:80]}")
    print(f"{_COLOR_BOLD}{'='*60}{_COLOR_RESET}")
    print_parsed(email.parsed, use_color)


def print_thread_json(thread: list[ThreadEmail]) -> None:
    output = []
    for email in thread:
        output.append({
            "date": email.date_str,
            "sender": email.sender,
            "subject": email.subject,
            "row_count": len(email.parsed.rows),
            "rows": [
                {
                    "division": r.division,
                    "brand_category": r.brand_category,
                    "availability": r.availability,
                    "milestone": r.milestone,
                    "milestone_ar": r.milestone_ar,
                    "shipment_bis": r.shipment_bis,
                    "comments": r.comments,
                    "comments_ar": r.comments_ar,
                    "language": r.language,
                }
                for r in email.parsed.rows
            ],
        })
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="DDS Email ETL - Process .eml files locally")
    parser.add_argument("path", help="Path to .eml file")
    parser.add_argument("--json", action="store_true", help="Output as JSON only")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--thread", action="store_true", help="Extract each email in thread separately by date")
    args = parser.parse_args()

    try:
        with open(args.path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    use_color = not args.no_color

    if args.thread:
        thread = extract_thread(raw)
        if args.json:
            print_thread_json(thread)
            return

        print(f"\n{_COLOR_BOLD}Thread contains {len(thread)} emails, sorted by date:{_COLOR_RESET}")
        for i, email in enumerate(thread, 1):
            print_thread_email(email, i, len(thread), use_color)
        return

    parsed = parse_email(raw)

    if args.json:
        output = {
            "subject": parsed.subject,
            "sender": parsed.sender,
            "date": parsed.date,
            "recipients": parsed.recipients,
            "row_count": len(parsed.rows),
            "rows": [
                {
                    "division": r.division,
                    "brand_category": r.brand_category,
                    "availability": r.availability,
                    "milestone": r.milestone,
                    "milestone_ar": r.milestone_ar,
                    "shipment_bis": r.shipment_bis,
                    "comments": r.comments,
                    "comments_ar": r.comments_ar,
                    "language": r.language,
                }
                for r in parsed.rows
            ],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print_parsed(parsed, use_color)
    print_extraction(parsed)

    print(f"{_COLOR_BOLD}Raw HTML size:{_COLOR_RESET} {len(parsed.raw_html)} bytes")
    print(f"{_COLOR_BOLD}Raw Text size:{_COLOR_RESET} {len(parsed.raw_text)} bytes")
    langs = set(r.language for r in parsed.rows)
    if langs:
        print(f"{_COLOR_BOLD}Languages detected:{_COLOR_RESET} {', '.join(sorted(langs))}")


if __name__ == "__main__":
    main()
