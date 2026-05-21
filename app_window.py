"""
Module B: Main application window — metadata form, sections, templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ai_guide_dialog import show_ai_template_guide
from core.template_engine import import_template_file, list_templates
from section_editor import SectionEditor
from worker import CompileWorker


class AppWindow(QMainWindow):
    def __init__(self, config: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._project_root = Path(config["project_root"])
        self._templates_path = Path(config["templates_dir"])
        self._worker: CompileWorker | None = None
        self._section_counter = 0
        self._setup_ui()
        self._reload_templates()
        self._add_section_tab("A", sample=True)

    def _setup_ui(self) -> None:
        self.setWindowTitle("Academic Helper — Question Paper")
        self.resize(1000, 720)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        meta_group = QGroupBox("Exam metadata")
        meta_form = QFormLayout(meta_group)
        self.title_input = QLineEdit("Sample Examination")
        self.subtitle_input = QLineEdit()
        self.institution_input = QLineEdit()
        self.duration_input = QSpinBox()
        self.duration_input.setRange(0, 600)
        self.duration_input.setSpecialValueText("—")
        self.duration_input.setValue(90)
        meta_form.addRow("Title *", self.title_input)
        meta_form.addRow("Subtitle", self.subtitle_input)
        meta_form.addRow("Institution", self.institution_input)
        meta_form.addRow("Duration (minutes)", self.duration_input)
        layout.addWidget(meta_group)

        sections_group = QGroupBox("Sections & questions")
        sections_layout = QVBoxLayout(sections_group)

        section_toolbar = QHBoxLayout()
        add_section_btn = QPushButton("Add section")
        add_section_btn.clicked.connect(self._add_section_dialog)
        remove_section_btn = QPushButton("Remove current section")
        remove_section_btn.clicked.connect(self._remove_current_section)
        section_toolbar.addWidget(add_section_btn)
        section_toolbar.addWidget(remove_section_btn)
        section_toolbar.addStretch()
        sections_layout.addLayout(section_toolbar)

        self.sections_tabs = QTabWidget()
        sections_layout.addWidget(self.sections_tabs)
        self.total_label = QLabel("Total marks: 0")
        sections_layout.addWidget(self.total_label)
        layout.addWidget(sections_group)

        template_group = QGroupBox("LaTeX template")
        template_layout = QHBoxLayout(template_group)
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)
        add_template_btn = QPushButton("Add template file…")
        add_template_btn.clicked.connect(self._import_template)
        open_folder_btn = QPushButton("Open templates folder")
        open_folder_btn.clicked.connect(self._open_templates_folder)
        template_layout.addWidget(QLabel("Active:"))
        template_layout.addWidget(self.template_combo, stretch=1)
        template_layout.addWidget(add_template_btn)
        template_layout.addWidget(open_folder_btn)
        layout.addWidget(template_group)

        action_layout = QHBoxLayout()
        self.ai_guide_btn = QPushButton("AI template guide (copy for ChatGPT)")
        self.ai_guide_btn.clicked.connect(self._show_ai_guide)
        self.generate_btn = QPushButton("Generate PDF")
        self.generate_btn.clicked.connect(self._start_generation)
        action_layout.addWidget(self.ai_guide_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.generate_btn)
        layout.addLayout(action_layout)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    def _reload_templates(self, select: str | None = None) -> None:
        current = select or self.template_combo.currentText()
        self.template_combo.clear()
        names = list_templates(self._templates_path)
        self.template_combo.addItems(names)
        if current:
            idx = self.template_combo.findText(current)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)

    def _selected_template(self) -> str:
        return self.template_combo.currentText() or "default"

    def _add_section_tab(self, code: str, *, sample: bool = False) -> SectionEditor:
        editor = SectionEditor(code)
        editor.set_marks_changed_callback(self._refresh_total)
        if sample:
            editor.add_sample_question()
        self.sections_tabs.addTab(editor, code)
        self.sections_tabs.setCurrentWidget(editor)
        self._refresh_total()
        return editor

    def _add_section_dialog(self) -> None:
        code, ok = QInputDialog.getText(
            self,
            "New section",
            "Section code (e.g. B, C):",
            text=chr(65 + self.sections_tabs.count()),
        )
        if not ok or not code.strip():
            return
        code = code.strip().upper()
        for i in range(self.sections_tabs.count()):
            widget = self.sections_tabs.widget(i)
            if isinstance(widget, SectionEditor) and widget.code_input.text().strip().upper() == code:
                QMessageBox.warning(self, "Duplicate", f"Section {code} already exists.")
                return
        self._add_section_tab(code)

    def _remove_current_section(self) -> None:
        idx = self.sections_tabs.currentIndex()
        if idx < 0:
            return
        if self.sections_tabs.count() <= 1:
            QMessageBox.warning(self, "Cannot remove", "At least one section is required.")
            return
        self.sections_tabs.removeTab(idx)
        self._refresh_total()

    def _refresh_total(self) -> None:
        total = 0
        for i in range(self.sections_tabs.count()):
            widget = self.sections_tabs.widget(i)
            if isinstance(widget, SectionEditor):
                total += widget.section_marks()
                code = widget.code_input.text().strip() or f"S{i + 1}"
                self.sections_tabs.setTabText(i, code)
        self.total_label.setText(f"Total marks: {total}")

    def _import_template(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select LaTeX template",
            str(self._templates_path),
            "LaTeX templates (*.template.tex *.tex);;All files (*.*)",
        )
        if not path_str:
            return

        default_name = Path(path_str).stem.replace(".template", "")
        name, ok = QInputDialog.getText(
            self,
            "Template name",
            "Save as (filename without extension):",
            text=default_name,
        )
        if not ok or not name.strip():
            return

        try:
            dest = import_template_file(
                Path(path_str),
                self._templates_path,
                name.strip(),
            )
        except (ValueError, FileExistsError) as exc:
            QMessageBox.warning(self, "Template not added", str(exc))
            return

        logical_name = dest.name[: -len(".template.tex")]
        self._reload_templates(select=logical_name)
        QMessageBox.information(
            self,
            "Template added",
            f"Saved as:\n{dest}\n\nSelected in the template list.",
        )

    def _open_templates_folder(self) -> None:
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

    def _show_ai_guide(self) -> None:
        try:
            sample = self._build_exam_data()
        except ValueError:
            sample = None
        show_ai_template_guide(
            self,
            project_root=self._project_root,
            templates_path=self._templates_path,
            template_name=self._selected_template(),
            sample_exam_data=sample,
        )

    def _build_exam_data(self) -> dict[str, Any]:
        title = self.title_input.text().strip()
        if not title:
            raise ValueError("Title is required.")
        if self.sections_tabs.count() < 1:
            raise ValueError("Add at least one section.")

        sections: list[dict[str, Any]] = []
        for i in range(self.sections_tabs.count()):
            widget = self.sections_tabs.widget(i)
            if isinstance(widget, SectionEditor):
                sections.append(widget.to_section_dict())

        total_marks = sum(
            sum(q["marks"] for q in s["questions"]) for s in sections
        )
        data: dict[str, Any] = {
            "title": title,
            "total_marks": total_marks,
            "sections": sections,
        }
        subtitle = self.subtitle_input.text().strip()
        institution = self.institution_input.text().strip()
        if subtitle:
            data["subtitle"] = subtitle
        if institution:
            data["institution"] = institution
        if self.duration_input.value() > 0:
            data["duration_minutes"] = self.duration_input.value()
        return data

    def _start_generation(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        try:
            exam_data = self._build_exam_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid input", str(exc))
            return

        self.generate_btn.setEnabled(False)
        self.statusBar().showMessage("Starting…")
        self._worker = CompileWorker(
            exam_data,
            tectonic_path=Path(self._config["tectonic_path"]),
            output_dir=Path(self._config["output_dir"]),
            template_name=self._selected_template(),
            project_root=self._project_root,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_succeeded)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_progress(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_succeeded(self, pdf_path: str) -> None:
        self.statusBar().showMessage(f"PDF saved: {pdf_path}")
        QMessageBox.information(self, "Success", f"Question paper generated:\n{pdf_path}")

    def _on_failed(self, message: str) -> None:
        self.statusBar().showMessage("Generation failed")
        QMessageBox.critical(self, "Generation failed", message)

    def _on_worker_finished(self) -> None:
        self.generate_btn.setEnabled(True)
        self._worker = None
