"""
Module A: Core thread controller — runs ingestion/compile off the UI thread.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

from core.compiler import compile_exam_paper


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
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._exam_data = exam_data
        self._tectonic_path = tectonic_path
        self._output_dir = output_dir
        self._template_name = template_name
        self._project_root = project_root

    def run(self) -> None:
        try:
            self.progress.emit("Validating exam data…")
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
