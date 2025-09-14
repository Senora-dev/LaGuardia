
# LaGuardia — Lightweight Policy‑as‑Code (MVP)

Guardrails for Terraform/OpenTofu **plan JSON** with **simple YAML rules** and **Auto‑Fix**.

[![LaGuardia Logo](https://raw.githubusercontent.com/senora-dev/laguardia/main/assets/logo.png)](https://raw.githubusercontent.com/Senora-dev/LaGuardia/main/assets/logo.png
)

## Install
```bash
pip install ./laguardia_mvp
```

## Usage
```bash
terraform init
terraform plan -out plan.out
terraform show -json plan.out > plan.json

laguardia scan --plan plan.json --rules examples/rules.yaml --out report.html --autofix fixes.json
# Exit code 1 if any 'error' findings
```

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
