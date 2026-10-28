import json
import subprocess
import sys
import zipfile
from pathlib import Path

import build_pages

ROOT = Path(__file__).resolve().parents[1]


def test_python_engine_bundle_is_self_contained_and_free_of_private_files(tmp_path):
    zip_path = tmp_path / "pyodide-app.zip"
    info = build_pages.bundle_python_engine(ROOT, zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert info["files"] == len(names)
        assert "app/technical.py" not in names
        assert "app/calculations/energisa.py" not in names
        assert "app/calculations/circuits.py" not in names
        assert "app/browser_runtime.py" in names
        assert "app/calculations/engine.py" in names
        assert "app/reports/assets/DejaVuSansMono.ttf" in names
        assert all(not n.endswith((".db", ".sqlite", ".sqlite3", ".pyc")) for n in names)
        extracted = tmp_path / "extracted"
        archive.extractall(extracted)

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import json, sys
from app.browser_runtime import dispatch_request
from app.schemas import CalculationInput
res = dispatch_request('GET', '/health')
project = CalculationInput(name='Casa planejada', property_stage='planned', environments=[dict(name='Sala', loads=[dict(name='TV', unit_power_w='100', parameters=dict(usage_hours_per_day='4', usage_days_per_month=30))])]).model_dump(mode='json')
calc = dispatch_request('POST', '/calculations/full', json.dumps(project))
assert calc['status'] == 200
result = calc['body']
assert result['monthly_energy']['value'] == '12'
assert dispatch_request('POST', '/projects', json.dumps(project))['status'] == 201
comparison = dispatch_request('POST', '/calculations/compare', json.dumps(dict(baseline=project, scenario=project)))
assert comparison['status'] == 200
assert comparison['body']['differences']['monthly_energy']['value'] == '0'
report = dict(project=project, expected_input_digest=result['input_digest'], expected_engine_version=result['engine_version'], expected_registry_version=result['technical_context']['registry_version'])
assert dispatch_request('POST', '/reports/pdf', json.dumps(report))['status'] == 200
assert 'app.technical' not in sys.modules
assert 'app.calculations.standards' not in sys.modules
print(json.dumps(res))
""",
        ],
        cwd=str(extracted),
        env={"PYTHONPATH": str(extracted)},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(probe.stdout)
    assert payload["status"] == 200
    assert payload["body"]["status"] == "ok"
