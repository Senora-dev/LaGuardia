
# LaGuardia - Lightweight Policy‑as‑Code (MVP)

Guardrails for Terraform/OpenTofu **plan JSON** with **simple YAML rules** and **Auto‑Fix**.

![LaguradiaLogo](assets/logo.png)  

## Install
```bash
pip install ./laguardia
```

Dev (editable) install for local changes:
```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
pip install -e .
```

## Usage
```bash
terraform init
terraform plan -out plan.out
terraform show -json plan.out > plan.json

laguardia scan --plan plan.json --rules examples/rules.yaml --out report.html --autofix fixes.json
# Exit code 1 if any 'error' findings
```

Alternative (one-liner) to produce plan.json:
```bash
terraform plan -out=plan.out && terraform show -json plan.out > plan.json && rm -f plan.out
```

Output semantics:
- Findings print as `[ERROR|WARNING] <rule> <type>.<name>: <message>`
- Final line prints `Run status: OK` or `Run status: FAIL`
- Control failing behavior via `--fail-on [error|warning|none]` (default: `error`)

## Rules (YAML)
See `examples/rules.yaml`. Supported kinds (MVP):
- `require_tags`: ensure tags/labels exist.
- `field_equals`: nested field equals a value.
- `forbid_cidr`: remove forbidden CIDR from list.

## Docker
```bash
docker build -t laguardia .
docker run --rm -v $(pwd):/data laguardia scan --plan /data/plan.json --rules /data/examples/rules.yaml --out /data/report.html --autofix /data/fixes.json
```

## Tests
```bash
pip install .
pip install pytest
pytest -q
```
## 🤝 Contributing
Maintained by [Senora.dev](https://senora.dev) - community contributions are welcome!
