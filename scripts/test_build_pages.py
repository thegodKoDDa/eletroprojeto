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
    assert info["files"] >= 25
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
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
            (
                "import json; "
                "from app.browser_runtime import dispatch_request; "
                "res = dispatch_request('GET', '/health'); "
                "print(json.dumps(res))"
            ),
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
