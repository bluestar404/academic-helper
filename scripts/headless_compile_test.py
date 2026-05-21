#!/usr/bin/env python3
"""
Headless end-to-end test: mock data -> models -> transpile -> paper.tex -> Tectonic PDF.

Run from project root:
    python scripts/headless_compile_test.py

Requires Tectonic in vendor/ (see vendor/README.md).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.compiler import compile_exam_paper
from core.models import ExamPaper
from core.transpiler import transpile

VENDOR_DIR = PROJECT_ROOT / "vendor"
TECTONIC_CANDIDATES = (
    VENDOR_DIR / "tectonic.exe",
    VENDOR_DIR / "tectonic",
)


def mock_exam_data() -> dict:
    """Raw exam payload with layout-breaking characters (sanitizer runs on validate)."""
    return {
        "title": "Sample Examination",
        "subtitle": "Computer Science - Semester II",
        "institution": "Academic Helper Demo College",
        "duration_minutes": 90,
        "total_marks": 20,
        "sections": [
            {
                "code": "A",
                "title": "Multiple Choice & Short Answer",
                "instructions": "Answer all questions. Marks shown in brackets.",
                "questions": [
                    {
                        "number": 1,
                        "text": "Define polymorphism & inheritance (50% weight).",
                        "marks": 5,
                    },
                    {
                        "number": 2,
                        "text": "Given $f(x) = x_1 + x_2$, solve the following:",
                        "marks": 10,
                        "sub_questions": [
                            {"label": "(a)", "text": "State the time complexity.", "marks": 4},
                            {"label": "(b)", "text": "Prove correctness for edge case $n=0$.", "marks": 6},
                        ],
                    },
                ],
            },
            {
                "code": "B",
                "title": "Long Answer",
                "instructions": "Attempt any one question.",
                "questions": [
                    {
                        "number": 1,
                        "text": "Discuss REST vs GraphQL. Use examples with $O(n)$ notation.",
                        "marks": 5,
                    },
                ],
            },
        ],
    }


def resolve_tectonic() -> Path:
    for candidate in TECTONIC_CANDIDATES:
        if candidate.is_file():
            return candidate
    names = ", ".join(p.name for p in TECTONIC_CANDIDATES)
    raise FileNotFoundError(
        f"Tectonic not found in {VENDOR_DIR}. "
        f"Place the binary as one of: {names}. See vendor/README.md."
    )


def run_tectonic(tectonic: Path, work_dir: Path, tex_name: str = "paper.tex") -> Path:
    """Invoke Tectonic; return path to generated PDF."""
    pdf_path = work_dir / "paper.pdf"

    result = subprocess.run(
        [str(tectonic), tex_name],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if not pdf_path.is_file():
        raise RuntimeError(f"Tectonic finished but {pdf_path} was not created.")
    return pdf_path


def compile_in_directory(
    work_dir: Path,
    latex: str,
    tectonic: Path,
) -> tuple[Path, Path]:
    tex_path = work_dir / "paper.tex"
    tex_path.write_text(latex, encoding="utf-8")
    pdf_path = run_tectonic(tectonic, work_dir)
    return tex_path, pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless PDF compile smoke test")
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temp directory after success (prints paths)",
    )
    args = parser.parse_args()

    print("1. Building mock exam data...")
    raw = mock_exam_data()

    print("2. Validating via Pydantic (sanitizer applied on text fields)...")
    paper = ExamPaper.model_validate(raw)
    assert paper.calculated_total_marks == paper.total_marks == 20

    print("3. Transpiling to LaTeX...")
    latex = transpile(paper, template_name="default", project_root=PROJECT_ROOT)

    print("4. Resolving Tectonic binary...")
    tectonic = resolve_tectonic()
    print(f"   Using: {tectonic}")

    output_dir = PROJECT_ROOT / "output" if args.keep_temp else None
    print("5. Compiling PDF...")
    _tex_path, pdf_path = compile_exam_paper(
        raw,
        tectonic=tectonic,
        output_dir=output_dir,
        template_name="default",
        project_root=PROJECT_ROOT,
    )

    print(f"\nSuccess: PDF generated at {pdf_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        if exc.stdout:
            print(exc.stdout)
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
