"""Build static GitHub Pages bundle with the embedded Python calculation engine."""

import argparse
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENGINE_MODULES = [
    "app/__init__.py",
    "app/version.py",
    "app/estimate_metadata.py",
    "app/locations.py",
    "app/schemas.py",
    "app/validation.py",
    "app/catalog.py",
    "app/equipment_relevance.py",
    "app/municipalities.py",
    "app/territory.py",
    "app/browser_runtime.py",
    "app/reports/__init__.py",
    "app/reports/summary.py",
    "app/reports/pdf.py",
    "app/reports/assets/DejaVuSansMono.ttf",
    "app/reports/assets/FONT-LICENSE.txt",
]


def engine_files(backend_root: Path) -> list[str]:
    # Explicit production surface: archived installation research is never shipped.
    calc_files = [
        f"app/calculations/{name}.py"
        for name in (
            "__init__",
            "engine",
            "equipment",
            "power",
            "energy",
            "current",
            "units",
            "comparison",
        )
    ]
    return sorted(set(ENGINE_MODULES + calc_files))


def bundle_python_engine(root: Path, destination_zip: Path) -> dict:
    backend_root = root / "backend"
    files = engine_files(backend_root)
    destination_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel_path in files:
            source = backend_root / rel_path
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"Módulo obrigatório do motor ausente ou inválido: {rel_path}")
            info = zipfile.ZipInfo(rel_path, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    return {"zip": str(destination_zip), "files": len(files)}


def build_pages(root: Path, output_dir: Path, base_path: str = "/eletroprojeto") -> dict:
    frontend_dir = root / "frontend"
    dist_rel = ".next/pages-build"
    dist_dir = frontend_dir / dist_rel
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)

    env = {
        **os.environ,
        "NEXT_OUTPUT_EXPORT": "1",
        "NEXT_DIST_DIR": dist_rel,
        "NEXT_BASE_PATH": base_path,
        "NEXT_PUBLIC_BASE_PATH": base_path,
        "NEXT_PUBLIC_BROWSER_RUNTIME": "1",
    }
    tsconfig_path = frontend_dir / "tsconfig.json"
    next_env_path = frontend_dir / "next-env.d.ts"
    tsconfig_before = tsconfig_path.read_bytes() if tsconfig_path.is_file() else None
    next_env_before = next_env_path.read_bytes() if next_env_path.is_file() else None
    try:
        subprocess.run(
            ["npm", "run", "build:webpack"],
            cwd=str(frontend_dir),
            env=env,
            check=True,
        )
    finally:
        if tsconfig_before is not None:
            tsconfig_path.write_bytes(tsconfig_before)
        if next_env_before is not None:
            next_env_path.write_bytes(next_env_before)

    export_source = dist_dir if (dist_dir / "index.html").is_file() else frontend_dir / "out"
    if not (export_source / "index.html").is_file():
        raise RuntimeError("Exportação estática do Next.js não gerou index.html.")

    shutil.copytree(export_source, output_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if (frontend_dir / "out").exists() and export_source == frontend_dir / "out":
        shutil.rmtree(frontend_dir / "out")

    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    bundle_info = bundle_python_engine(root, output_dir / "pyodide-app.zip")
    return {
        "output": str(output_dir),
        "base_path": base_path,
        "engine_files": bundle_info["files"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "frontend/.next/pages-out",
        help="Diretório de saída da publicação estática.",
    )
    parser.add_argument(
        "--base-path",
        default="/eletroprojeto",
        help="Caminho base no GitHub Pages (vazio para raiz).",
    )
    parser.add_argument(
        "--bundle-only",
        type=Path,
        default=None,
        help="Gerar apenas o arquivo pyodide-app.zip no caminho informado.",
    )
    args = parser.parse_args()
    if args.bundle_only is not None:
        result = bundle_python_engine(ROOT, args.bundle_only)
    else:
        result = build_pages(ROOT, args.output.resolve(), args.base_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
