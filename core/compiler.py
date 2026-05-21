"""Headless compile pipeline: validate, transpile, write .tex, run Tectonic."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from core.models import ExamPaper
from core.transpiler import transpile

VENDOR_DIR_NAME = "vendor"
TECTONIC_CANDIDATES = ("tectonic.exe", "tectonic")


def resolve_tectonic(project_root: Path, configured: str | None = None) -> Path:
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = project_root / path
        if path.is_file():
            return path
        raise FileNotFoundError(f"Configured Tectonic not found: {path}")

    vendor = project_root / VENDOR_DIR_NAME
    for name in TECTONIC_CANDIDATES:
        candidate = vendor / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Tectonic not found under {vendor}. See vendor/README.md."
    )


def run_tectonic(tectonic: Path, work_dir: Path, tex_name: str = "paper.tex") -> Path:
    pdf_path = work_dir / "paper.pdf"
    subprocess.run(
        [str(tectonic), tex_name],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    if not pdf_path.is_file():
        raise RuntimeError(f"Tectonic finished but {pdf_path} was not created.")
    return pdf_path


def compile_exam_paper(
    exam_data: dict,
    *,
    tectonic: Path,
    output_dir: Path | None = None,
    template_name: str = "default",
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """
    Full pipeline in the current thread (for worker.run).

    Returns (tex_path, pdf_path). Copies PDF to output_dir when provided.
    """
    paper = ExamPaper.model_validate(exam_data)
    if project_root is None:
        raise ValueError("project_root is required for template resolution")
    latex = transpile(paper, template_name=template_name, project_root=project_root)

    work_dir = Path(tempfile.mkdtemp(prefix="academic_helper_"))
    tex_path = work_dir / "paper.tex"
    tex_path.write_text(latex, encoding="utf-8")
    pdf_path = run_tectonic(tectonic, work_dir)

    final_pdf = pdf_path
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        final_pdf = output_dir / "paper.pdf"
        shutil.copy2(pdf_path, final_pdf)
        shutil.rmtree(work_dir, ignore_errors=True)
    return tex_path, final_pdf
