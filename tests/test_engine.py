
import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from laguardia.engine import run_scan

def make_demo_plan(tmp_path):
    plan = {
      "planned_values": {
        "root_module": {
          "resources": [
            {"type": "aws_s3_bucket", "name": "demo_bucket",
             "values": {"server_side_encryption_configuration": {}}},
            {"type": "aws_security_group_rule", "name": "demo_sg_rule",
             "values": {"cidr_blocks": ["0.0.0.0/0"]}},
            {"type": "aws_ebs_volume", "name": "demo_ebs",
             "values": {"encrypted": False}},
            {"type": "aws_db_instance", "name": "demo_rds",
             "values": {"backup_retention_period": 0}},
            {"type": "aws_vpc", "name": "demo_vpc",
             "values": {"tags": {"env": "dev"}}}
          ]
        }
      }
    }
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan))
    return str(p)

def rules_path(project_root):
    return os.path.join(project_root, "examples", "rules.yaml")

def test_scan_finds_issues(tmp_path):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    plan = make_demo_plan(tmp_path)
    report = str(tmp_path / "report.html")
    findings = run_scan(plan, rules_path(project_root), report)
    rule_ids = {f["rule_id"] for f in findings}
    assert "tags.required" in rule_ids
    assert "aws.s3.encrypted" in rule_ids
    assert "aws.sg.no-wide-open" in rule_ids

def test_autofix_json_created(tmp_path):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    plan = make_demo_plan(tmp_path)
    report = str(tmp_path / "report.html")
    fixes = str(tmp_path / "fixes.json")
    _ = run_scan(plan, rules_path(project_root), report, fixes)
    assert os.path.exists(fixes)
    data = json.loads(open(fixes).read())
    assert "aws_ebs_volume.demo_ebs" in data
    assert data["aws_ebs_volume.demo_ebs"]["encrypted"] == True
