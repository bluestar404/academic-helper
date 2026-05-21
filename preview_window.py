"""Floating PDF preview window."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView

    _HAS_PDF = True
except ImportError:
    _HAS_PDF = False


class PreviewWindow(QDialog):
    """Mini window showing the compiled PDF."""

    def __init__(
        self,
        pdf_path: str | Path,
        *,
        work_dir: Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._pdf_path = Path(pdf_path)
        self._work_dir = work_dir
        self.setWindowTitle("Preview — Question Paper")
        self.resize(520, 720)
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)
        header = QLabel("Live preview (current form + template)")
        header.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(header)

        if _HAS_PDF and self._pdf_path.is_file():
            self._doc = QPdfDocument(self)
            self._view = QPdfView(self)
            err = self._doc.load(str(self._pdf_path.resolve()))
            if err != QPdfDocument.Error.None_:
                layout.addWidget(QLabel(f"Could not load PDF: {self._pdf_path}"))
            else:
                self._view.setDocument(self._doc)
                self._view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
                layout.addWidget(self._view, stretch=1)
        else:
            msg = (
                "PDF preview requires PySide6 QtPdf support.\n\n"
                f"File saved at:\n{self._pdf_path.resolve()}"
            )
            layout.addWidget(QLabel(msg))

        buttons = QHBoxLayout()
        open_btn = QPushButton("Open in system viewer")
        open_btn.clicked.connect(self._open_external)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(open_btn)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _open_external(self) -> None:
        import os
        import subprocess
        import sys

        path = str(self._pdf_path.resolve())
        if not self._pdf_path.is_file():
            QMessageBox.warning(self, "Missing file", path)
            return
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

    def closeEvent(self, event) -> None:
        if self._work_dir and self._work_dir.is_dir():
            shutil.rmtree(self._work_dir, ignore_errors=True)
        super().closeEvent(event)
