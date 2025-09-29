
import argparse, sys
from .engine import run_scan

def main():
    parser = argparse.ArgumentParser(prog="laguardia", description="LaGuardia - Lightweight Policy-as-Code for Terraform/OpenTofu")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Scan a Terraform plan JSON with YAML rules")
    scan.add_argument("--plan", required=True, help="Path to terraform show -json output")
    scan.add_argument("--rules", required=True, help="Path to YAML rules file")
    scan.add_argument("--out", help="Path to HTML report output (optional)")
    scan.add_argument("--autofix", help="Path to JSON autofix output (optional)")
    scan.add_argument("--fail-on", choices=["error","warning","none"], default="error", help="Severity to fail the run on")

    args = parser.parse_args()

    if args.cmd == "scan":
        findings = run_scan(args.plan, args.rules, args.out, args.autofix)
        if args.fail_on == "none":
            print("Run status: OK")
            sys.exit(0)
        levels = {"warning": 1, "error": 2}
        threshold = levels[args.fail_on]
        worst = 0
        for f in findings:
            worst = max(worst, levels.get(f.get("level","warning"), 1))
        if worst >= threshold and findings:
            print("Run status: FAIL")
            sys.exit(1)
        else:
            print("Run status: OK" + (" (issues found)" if findings else " (no issues)"))
            sys.exit(0)

if __name__ == "__main__":
    main()