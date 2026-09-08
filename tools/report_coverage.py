"""Display separate statement and branch totals from a coverage.py JSON report."""

import json
import sys
from pathlib import Path


def main() -> None:
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not report["meta"]["branch_coverage"]:
        raise SystemExit("Expected a branch coverage report")
    totals = report["totals"]
    print("| Coverage | Covered | Total | Percent | Policy |")
    print("| --- | ---: | ---: | ---: | --- |")
    for label, covered, total, policy in (
        (
            "Statements",
            totals["covered_lines"],
            totals["num_statements"],
            "100% required by `make test`",
        ),
        (
            "Branches",
            totals["covered_branches"],
            totals["num_branches"],
            "Reporting only",
        ),
    ):
        percent = f"{100 * covered / total:.2f}%" if total else "n/a"
        print(f"| {label} | {covered} | {total} | {percent} | {policy} |")


if __name__ == "__main__":
    main()
