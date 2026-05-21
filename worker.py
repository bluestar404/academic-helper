"""
Module A: Core thread controller — runs ingestion/compile off the UI thread.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

from core.compiler import compile_exam_paper, run_tectonic
from core.models import ExamPaper
from core.transpiler import transpile


class CompileWorker(QThread):
    """Pipeline manager: validate → transpile → filesystem → Tectonic."""

    progress = Signal(str)
    succeeded = Signal(str)  # final PDF path
    failed = Signal(str)

    def __init__(
        self,
        exam_data: dict[str, Any],
        *,
        tectonic_path: Path,
        output_dir: Path | None = None,
        template_name: str = "default",
        project_root: Path | None = None,
        preview_only: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._exam_data = exam_data
        self._tectonic_path = tectonic_path
        self._output_dir = output_dir
        self._template_name = template_name
        self._project_root = project_root
        self._preview_only = preview_only

    def run(self) -> None:
        try:
            self.progress.emit("Validating exam data…")
            if self._preview_only:
                self._run_preview()
                return
            self.progress.emit("Transpiling LaTeX…")
            self.progress.emit("Writing sources and running Tectonic…")
            _tex_path, pdf_path = compile_exam_paper(
                self._exam_data,
                tectonic=self._tectonic_path,
                output_dir=self._output_dir,
                template_name=self._template_name,
                project_root=self._project_root,
            )
            self.progress.emit("Done.")
            self.succeeded.emit(str(pdf_path.resolve()))
        except Exception as exc:
            self.failed.emit(str(exc))

    def _run_preview(self) -> None:
        self.progress.emit("Building preview…")
        paper = ExamPaper.model_validate(self._exam_data)
        latex = transpile(
            paper,
            template_name=self._template_name,
            project_root=self._project_root,
        )
        work_dir = Path(tempfile.mkdtemp(prefix="academic_helper_preview_"))
        tex_path = work_dir / "paper.tex"
        tex_path.write_text(latex, encoding="utf-8")
        self.progress.emit("Compiling PDF…")
        pdf_path = run_tectonic(self._tectonic_path, work_dir)
        self.progress.emit("Preview ready.")
        self.succeeded.emit(f"{pdf_path.resolve()}|{work_dir.resolve()}")


class PreviewWorker(CompileWorker):
    """Shorthand for preview-only compilation."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs["preview_only"] = True
        kwargs["output_dir"] = None
        super().__init__(*args, **kwargs)
