"""Template picker, source peek, and preview controls."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ai_guide_dialog import show_ai_template_guide
from core.template_engine import (
    import_template_file,
    list_templates,
    load_template,
    normalize_template_name,
    validate_template_source,
)

TEMPLATE_BLURBS = {
    "default": "Modern header, colored sections, booktabs tables",
    "classic": "Centered rules, traditional exam layout",
    "minimal": "Full pass-through — only {{FULL_DOCUMENT}}",
    "sppu_original": "SPPU / Pune University — Q1) a) b) with OR blocks",
}


class TemplatePanel(QGroupBox):
    template_changed = Signal(str)

    def __init__(
        self,
        *,
        templates_path: Path,
        project_root: Path,
        get_exam_data: Callable[[], dict[str, Any]],
        on_preview: Callable[[str], None],
        parent=None,
    ) -> None:
        super().__init__("Layout & templates", parent)
        self._templates_path = templates_path
        self._project_root = project_root
        self._get_exam_data = get_exam_data
        self._on_preview = on_preview

        layout = QVBoxLayout(self)

        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.template_list)

        self.source_peek = QPlainTextEdit()
        self.source_peek.setReadOnly(True)
        self.source_peek.setMaximumHeight(140)
        self.source_peek.setPlaceholderText("Template source preview…")
        layout.addWidget(self.source_peek)

        row1 = QHBoxLayout()
        import_btn = QPushButton("Import .tex…")
        import_btn.clicked.connect(self._import_template)
        folder_btn = QPushButton("Folder")
        folder_btn.clicked.connect(self._open_folder)
        row1.addWidget(import_btn)
        row1.addWidget(folder_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.preview_btn = QPushButton("Preview PDF")
        self.preview_btn.setObjectName("previewBtn")
        self.preview_btn.clicked.connect(self._request_preview)
        guide_btn = QPushButton("AI guide")
        guide_btn.clicked.connect(self._show_guide)
        row2.addWidget(self.preview_btn)
        row2.addWidget(guide_btn)
        layout.addLayout(row2)

        self.reload()

    def selected_template(self) -> str:
        item = self.template_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else "default"

    def reload(self, select: str | None = None) -> None:
        current = select or self.selected_template()
        self.template_list.clear()
        for name in list_templates(self._templates_path):
            blurb = TEMPLATE_BLURBS.get(name, "Custom template")
            item = QListWidgetItem(f"{name}\n{blurb}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.template_list.addItem(item)
        for i in range(self.template_list.count()):
            if self.template_list.item(i).data(Qt.ItemDataRole.UserRole) == current:
                self.template_list.setCurrentRow(i)
                break
        else:
            if self.template_list.count():
                self.template_list.setCurrentRow(0)
        self._refresh_peek()

    def _on_selection_changed(self) -> None:
        self._refresh_peek()
        self.template_changed.emit(self.selected_template())

    def _refresh_peek(self) -> None:
        try:
            name = self.selected_template()
            source = load_template(self._templates_path, name)
            warnings = validate_template_source(source, strict=False)
            note = ""
            if warnings:
                note = "\n\n-- " + " | ".join(warnings[:2])
            preview = source[:1200] + ("…" if len(source) > 1200 else "")
            self.source_peek.setPlainText(preview + note)
        except Exception as exc:
            self.source_peek.setPlainText(str(exc))

    def _import_template(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Import LaTeX template",
            str(self._templates_path),
            "LaTeX (*.template.tex *.tex);;All files (*)",
        )
        if not path_str:
            return
        name, ok = QInputDialog.getText(
            self,
            "Template name",
            "Save as:",
            text=Path(path_str).stem.replace(".template", ""),
        )
        if not ok or not name.strip():
            return
        try:
            dest = import_template_file(
                Path(path_str),
                self._templates_path,
                name.strip(),
                strict=False,
            )
        except FileExistsError:
            overwrite = QMessageBox.question(
                self,
                "Exists",
                "Template exists. Overwrite?",
            )
            if overwrite != QMessageBox.StandardButton.Yes:
                return
            dest = self._templates_path / f"{normalize_template_name(name)}.template.tex"
            dest.write_text(Path(path_str).read_text(encoding="utf-8"), encoding="utf-8")
        except ValueError as exc:
            QMessageBox.warning(self, "Import issue", str(exc))
            return

        logical = dest.name[: -len(".template.tex")]
        self.reload(select=logical)
        QMessageBox.information(self, "Imported", f"Template ready: {dest.name}")

    def _open_folder(self) -> None:
        self._templates_path.mkdir(parents=True, exist_ok=True)
        import os
        import subprocess
        import sys

        path = str(self._templates_path.resolve())
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

    def _show_guide(self) -> None:
        try:
            sample = self._get_exam_data()
        except ValueError:
            sample = None
        show_ai_template_guide(
            self,
            project_root=self._project_root,
            templates_path=self._templates_path,
            template_name=self.selected_template(),
            sample_exam_data=sample,
        )

    def _request_preview(self) -> None:
        self._on_preview(self.selected_template())
