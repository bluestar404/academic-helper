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
COL_PARTS = 2
COL_MARKS = 3
PARTS_SEP = ";"
PART_FIELD_SEP = "|"


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

        self.questions_table = QTableWidget(0, 4)
        self.questions_table.setHorizontalHeaderLabels(
            ["#", "Question / stem", "Sub-parts (a|text|5;b|...)", "Marks"]
        )
        self.questions_table.horizontalHeader().setSectionResizeMode(
            COL_TEXT, QHeaderView.ResizeMode.Stretch
        )
        self.questions_table.horizontalHeader().setSectionResizeMode(
            COL_PARTS, QHeaderView.ResizeMode.Stretch
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
        self.questions_table.setItem(row, COL_PARTS, QTableWidgetItem(""))
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
            parts_cell = ""
            if q.get("sub_questions"):
                chunks = []
                for sq in q["sub_questions"]:
                    label = sq.get("label", "a").rstrip(")")
                    chunks.append(
                        f"{label}{PART_FIELD_SEP}{sq.get('text', '')}"
                        f"{PART_FIELD_SEP}{sq.get('marks', 1)}"
                    )
                parts_cell = PARTS_SEP.join(chunks)
            self.questions_table.setItem(row, COL_PARTS, QTableWidgetItem(parts_cell))
            self.questions_table.setItem(
                row, COL_MARKS, QTableWidgetItem(str(q.get("marks", 1)))
            )

    @staticmethod
    def _parse_sub_parts(raw: str) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = []
        for chunk in raw.split(PARTS_SEP):
            chunk = chunk.strip()
            if not chunk:
                continue
            fields = [f.strip() for f in chunk.split(PART_FIELD_SEP)]
            if len(fields) < 3:
                raise ValueError(
                    "Sub-parts format: label|text|marks separated by ';' "
                    "(e.g. a|Define locks|5;b|Explain RMI|5)"
                )
            label, text, marks_s = fields[0], fields[1], fields[2]
            if not marks_s.isdigit() or int(marks_s) < 1:
                raise ValueError("Sub-part marks must be positive integers.")
            label_fmt = label if label.endswith(")") else f"{label})"
            parts.append(
                {"label": label_fmt, "text": text, "marks": int(marks_s)}
            )
        return parts

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
            parts_item = self.questions_table.item(row, COL_PARTS)
            marks_item = self.questions_table.item(row, COL_MARKS)
            num_item = self.questions_table.item(row, COL_NUMBER)
            text = (text_item.text() if text_item else "").strip()
            parts_raw = (parts_item.text() if parts_item else "").strip()
            if not text and not parts_raw:
                continue
            if not text:
                text = " "
            marks_raw = (marks_item.text() if marks_item else "").strip()
            if not marks_raw.isdigit() or int(marks_raw) < 1:
                raise ValueError(
                    f"Section {code}, row {row + 1}: marks must be a positive integer."
                )
            number = int((num_item.text() if num_item else "").strip() or row + 1)
            entry: dict[str, Any] = {
                "number": number,
                "text": text,
                "marks": int(marks_raw),
            }
            if parts_raw:
                entry["sub_questions"] = self._parse_sub_parts(parts_raw)
                if sum(p["marks"] for p in entry["sub_questions"]) != entry["marks"]:
                    raise ValueError(
                        f"Section {code}, Q{number}: marks must equal sum of sub-parts."
                    )
            questions.append(entry)

        if not questions:
            raise ValueError(f"Section {code}: add at least one question.")

        instructions = self.instructions_input.text().strip()
        return {
            "code": code,
            "title": title,
            "instructions": instructions or None,
            "questions": questions,
        }

    def add_sample_question(self, *, sppu_style: bool = False) -> None:
        if self.questions_table.rowCount() == 0:
            self._add_row()
        self.questions_table.setItem(0, COL_NUMBER, QTableWidgetItem("1"))
        if sppu_style:
            self.instructions_input.setText(
                "Answer Q.1 or Q.2, Q.3 or Q.4; Figures to the right indicate full marks.; "
                "Assume suitable data, if necessary."
            )
            self.questions_table.setItem(0, COL_TEXT, QTableWidgetItem(" "))
            self.questions_table.setItem(
                0,
                COL_PARTS,
                QTableWidgetItem(
                    "a|What are Locks? Explain Distributed Lock services using Timestamps.|5;"
                    "b|What is JAVA RMI? How do we create Java RMI? Similarity with web service?|5"
                ),
            )
            self.questions_table.setItem(0, COL_MARKS, QTableWidgetItem("10"))
            self._add_row()
            self.questions_table.setItem(1, COL_NUMBER, QTableWidgetItem("2"))
            self.questions_table.setItem(1, COL_TEXT, QTableWidgetItem(" "))
            self.questions_table.setItem(
                1,
                COL_PARTS,
                QTableWidgetItem(
                    "a|Explain single-copy and Multi-copy distributed shared memory.|5;"
                    "b|Define Service oriented architecture. List four SOA characteristics.|5"
                ),
            )
            self.questions_table.setItem(1, COL_MARKS, QTableWidgetItem("10"))
        else:
            self.questions_table.setItem(
                0,
                COL_TEXT,
                QTableWidgetItem("Define polymorphism and inheritance."),
            )
            self.questions_table.setItem(0, COL_MARKS, QTableWidgetItem("5"))
