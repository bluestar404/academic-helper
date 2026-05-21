"""
Module B: Main application window — metadata, sections, templates, preview.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from preview_window import PreviewWindow
from section_editor import SectionEditor
from template_panel import TemplatePanel
from worker import CompileWorker, PreviewWorker


class AppWindow(QMainWindow):
    def __init__(self, config: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._project_root = Path(config["project_root"])
        self._templates_path = Path(config["templates_dir"])
        self._worker: CompileWorker | None = None
        self._preview_window: PreviewWindow | None = None
        self._setup_ui()
        self._add_section_tab("A", sample=True, sppu_style=True)

    def _setup_ui(self) -> None:
        self.setWindowTitle("Academic Helper")
        self.resize(1180, 760)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 4, 8)

        meta_group = QGroupBox("Exam details")
        meta_form = QFormLayout(meta_group)
        self.title_input = QLineEdit("C : Advanced Computer Programming")
        self.subtitle_input = QLineEdit("B.E. (Computer Engg.) (Semester - I)")
        self.institution_input = QLineEdit("(2012 Pattern) (Elective - I)")
        self.paper_code_input = QLineEdit("P3556")
        self.exam_code_input = QLineEdit("[4959] - 1156")
        self.time_display_input = QLineEdit("2 1/2 Hours")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(0, 600)
        self.duration_input.setSpecialValueText("—")
        self.duration_input.setValue(0)
        meta_form.addRow("Subject / Title *", self.title_input)
        meta_form.addRow("Course line", self.subtitle_input)
        meta_form.addRow("Pattern line", self.institution_input)
        meta_form.addRow("Paper code", self.paper_code_input)
        meta_form.addRow("Exam code", self.exam_code_input)
        meta_form.addRow("Time (display)", self.time_display_input)
        meta_form.addRow("Duration (min)", self.duration_input)
        left_layout.addWidget(meta_group)

        sections_group = QGroupBox("Sections & questions")
        sections_layout = QVBoxLayout(sections_group)
        section_toolbar = QHBoxLayout()
        add_section_btn = QPushButton("+ Section")
        add_section_btn.clicked.connect(self._add_section_dialog)
        remove_section_btn = QPushButton("− Section")
        remove_section_btn.clicked.connect(self._remove_current_section)
        section_toolbar.addWidget(add_section_btn)
        section_toolbar.addWidget(remove_section_btn)
        section_toolbar.addStretch()
        sections_layout.addLayout(section_toolbar)

        self.sections_tabs = QTabWidget()
        sections_layout.addWidget(self.sections_tabs)
        self.total_label = QLabel("Total marks: 0")
        self.total_label.setObjectName("totalMarks")
        sections_layout.addWidget(self.total_label)
        left_layout.addWidget(sections_group, stretch=1)

        action_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate PDF")
        self.generate_btn.setObjectName("primaryBtn")
        self.generate_btn.clicked.connect(self._start_generation)
        action_layout.addStretch()
        action_layout.addWidget(self.generate_btn)
        left_layout.addLayout(action_layout)

        splitter.addWidget(left)

        self.template_panel = TemplatePanel(
            templates_path=self._templates_path,
            project_root=self._project_root,
            get_exam_data=self._build_exam_data,
            on_preview=self._start_preview,
        )
        self.template_panel.template_changed.connect(self._on_template_changed)
        splitter.addWidget(self.template_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — pick a template and preview anytime")

    def _on_template_changed(self, _name: str) -> None:
        self.statusBar().showMessage(f"Template: {self.template_panel.selected_template()}")

    def _add_section_tab(
        self, code: str, *, sample: bool = False, sppu_style: bool = False
    ) -> SectionEditor:
        editor = SectionEditor(code)
        editor.set_marks_changed_callback(self._refresh_total)
        if sample:
            editor.add_sample_question(sppu_style=sppu_style)
        self.sections_tabs.addTab(editor, code)
        self.sections_tabs.setCurrentWidget(editor)
        self._refresh_total()
        return editor

    def _add_section_dialog(self) -> None:
        code, ok = QInputDialog.getText(
            self,
            "New section",
            "Section code:",
            text=chr(65 + self.sections_tabs.count()),
        )
        if not ok or not code.strip():
            return
        code = code.strip().upper()
        for i in range(self.sections_tabs.count()):
            w = self.sections_tabs.widget(i)
            if isinstance(w, SectionEditor) and w.code_input.text().strip().upper() == code:
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

        total_marks = sum(sum(q["marks"] for q in s["questions"]) for s in sections)
        data: dict[str, Any] = {
            "title": title,
            "total_marks": total_marks,
            "sections": sections,
        }
        if self.subtitle_input.text().strip():
            data["subtitle"] = self.subtitle_input.text().strip()
        if self.institution_input.text().strip():
            data["institution"] = self.institution_input.text().strip()
        if self.duration_input.value() > 0:
            data["duration_minutes"] = self.duration_input.value()
        if self.paper_code_input.text().strip():
            data["paper_code"] = self.paper_code_input.text().strip()
        if self.exam_code_input.text().strip():
            data["exam_code"] = self.exam_code_input.text().strip()
        if self.time_display_input.text().strip():
            data["time_display"] = self.time_display_input.text().strip()
        return data

    def _start_preview(self, template_name: str) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        try:
            exam_data = self._build_exam_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot preview", str(exc))
            return

        self.template_panel.preview_btn.setEnabled(False)
        self.statusBar().showMessage("Compiling preview…")
        self._worker = PreviewWorker(
            exam_data,
            tectonic_path=Path(self._config["tectonic_path"]),
            template_name=template_name,
            project_root=self._project_root,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_preview_succeeded)
        self._worker.failed.connect(self._on_preview_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_preview_succeeded(self, payload: str) -> None:
        if "|" in payload:
            pdf_path, work_dir = payload.split("|", 1)
            work_path = Path(work_dir)
        else:
            pdf_path, work_path = payload, None

        if self._preview_window:
            self._preview_window.close()
        self._preview_window = PreviewWindow(
            pdf_path,
            work_dir=work_path,
            parent=self,
        )
        self._preview_window.show()
        self.statusBar().showMessage("Preview open")

    def _on_preview_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Preview failed", message)

    def _start_generation(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        try:
            exam_data = self._build_exam_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid input", str(exc))
            return

        self.generate_btn.setEnabled(False)
        self.statusBar().showMessage("Generating PDF…")
        self._worker = CompileWorker(
            exam_data,
            tectonic_path=Path(self._config["tectonic_path"]),
            output_dir=Path(self._config["output_dir"]),
            template_name=self.template_panel.selected_template(),
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
        if "|" in pdf_path:
            pdf_path = pdf_path.split("|", 1)[0]
        self.statusBar().showMessage(f"Saved: {pdf_path}")
        QMessageBox.information(self, "Success", f"Question paper saved:\n{pdf_path}")

    def _on_failed(self, message: str) -> None:
        self.statusBar().showMessage("Failed")
        QMessageBox.critical(self, "Generation failed", message)

    def _on_worker_finished(self) -> None:
        self.generate_btn.setEnabled(True)
        self.template_panel.preview_btn.setEnabled(True)
        self._worker = None
