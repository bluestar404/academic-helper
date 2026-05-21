"""Single exam section: metadata fields + questions table."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

COL_NUMBER = 0
COL_TEXT = 1
COL_MARKS = 2


class SectionEditor(QWidget):
    def __init__(self, code: str = "A", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.code_input = QLineEdit(code)
        self.title_input = QLineEdit(f"Section {code}")
        self.instructions_input = QLineEdit("Answer all questions.")
        form.addRow("Code *", self.code_input)
        form.addRow("Title *", self.title_input)
        form.addRow("Instructions", self.instructions_input)
        layout.addLayout(form)

        self.questions_table = QTableWidget(0, 3)
        self.questions_table.setHorizontalHeaderLabels(["#", "Question text", "Marks"])
        self.questions_table.horizontalHeader().setSectionResizeMode(
            COL_TEXT, QHeaderView.ResizeMode.Stretch
        )
        self.questions_table.horizontalHeader().setSectionResizeMode(
            COL_NUMBER, QHeaderView.ResizeMode.ResizeToContents
        )
        self.questions_table.horizontalHeader().setSectionResizeMode(
            COL_MARKS, QHeaderView.ResizeMode.ResizeToContents
        )
        self.questions_table.itemChanged.connect(self._emit_marks_changed)
        layout.addWidget(self.questions_table)

        buttons = QHBoxLayout()
        add_btn = QPushButton("Add question")
        add_btn.clicked.connect(self._add_row)
        remove_btn = QPushButton("Remove question")
        remove_btn.clicked.connect(self._remove_row)
        buttons.addWidget(add_btn)
        buttons.addWidget(remove_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        self._marks_callback = None

    def set_marks_changed_callback(self, callback) -> None:
        self._marks_callback = callback

    def _emit_marks_changed(self, *_args) -> None:
        if self._marks_callback:
            self._marks_callback()

    def section_marks(self) -> int:
        total = 0
        for row in range(self.questions_table.rowCount()):
            item = self.questions_table.item(row, COL_MARKS)
            if item and item.text().strip().isdigit():
                total += int(item.text().strip())
        return total

    def _add_row(self) -> None:
        row = self.questions_table.rowCount()
        self.questions_table.insertRow(row)
        self.questions_table.setItem(row, COL_NUMBER, QTableWidgetItem(str(row + 1)))
        self.questions_table.setItem(row, COL_TEXT, QTableWidgetItem(""))
        self.questions_table.setItem(row, COL_MARKS, QTableWidgetItem("5"))
        self._emit_marks_changed()

    def _remove_row(self) -> None:
        row = self.questions_table.currentRow()
        if row < 0 and self.questions_table.rowCount():
            row = self.questions_table.rowCount() - 1
        if row >= 0:
            self.questions_table.removeRow(row)
        self._emit_marks_changed()

    def load_section_data(self, data: dict[str, Any] | None = None) -> None:
        if not data:
            return
        self.code_input.setText(data.get("code", "A"))
        self.title_input.setText(data.get("title", ""))
        self.instructions_input.setText(data.get("instructions") or "")
        self.questions_table.setRowCount(0)
        for q in data.get("questions", []):
            row = self.questions_table.rowCount()
            self.questions_table.insertRow(row)
            self.questions_table.setItem(
                row, COL_NUMBER, QTableWidgetItem(str(q.get("number", row + 1)))
            )
            self.questions_table.setItem(
                row, COL_TEXT, QTableWidgetItem(q.get("text", ""))
            )
            self.questions_table.setItem(
                row, COL_MARKS, QTableWidgetItem(str(q.get("marks", 1)))
            )

    def to_section_dict(self) -> dict[str, Any]:
        code = self.code_input.text().strip()
        title = self.title_input.text().strip()
        if not code:
            raise ValueError("Each section needs a code (e.g. A, B).")
        if not title:
            raise ValueError(f"Section {code or '?'} needs a title.")

        questions: list[dict[str, Any]] = []
        for row in range(self.questions_table.rowCount()):
            text_item = self.questions_table.item(row, COL_TEXT)
            marks_item = self.questions_table.item(row, COL_MARKS)
            num_item = self.questions_table.item(row, COL_NUMBER)
            text = (text_item.text() if text_item else "").strip()
            if not text:
                continue
            marks_raw = (marks_item.text() if marks_item else "").strip()
            if not marks_raw.isdigit() or int(marks_raw) < 1:
                raise ValueError(
                    f"Section {code}, row {row + 1}: marks must be a positive integer."
                )
            number = int((num_item.text() if num_item else "").strip() or row + 1)
            questions.append(
                {"number": number, "text": text, "marks": int(marks_raw)}
            )

        if not questions:
            raise ValueError(f"Section {code}: add at least one question.")

        instructions = self.instructions_input.text().strip()
        return {
            "code": code,
            "title": title,
            "instructions": instructions or None,
            "questions": questions,
        }

    def add_sample_question(self) -> None:
        if self.questions_table.rowCount() == 0:
            self._add_row()
        self.questions_table.setItem(0, COL_NUMBER, QTableWidgetItem("1"))
        self.questions_table.setItem(
            0,
            COL_TEXT,
            QTableWidgetItem("Define polymorphism and inheritance."),
        )
        self.questions_table.setItem(0, COL_MARKS, QTableWidgetItem("5"))
