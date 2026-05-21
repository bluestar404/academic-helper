"""Dialog: architecture instructions + active template for ChatGPT."""

from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from core.models import ExamPaper
from core.template_engine import build_chatgpt_prompt, load_template, normalize_template_name
from core.transpiler import build_render_context


def show_ai_template_guide(
    parent,
    *,
    project_root: Path,
    templates_path: Path,
    template_name: str,
    sample_exam_data: dict | None = None,
) -> None:
    try:
        prompt = _build_guide_text(
            templates_path=templates_path,
            template_name=template_name,
            sample_exam_data=sample_exam_data,
        )
    except Exception as exc:
        QMessageBox.critical(
            parent,
            "Template guide failed",
            f"Could not build the guide:\n\n{exc}\n\n{traceback.format_exc()}",
        )
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle("AI template guide — copy to ChatGPT")
    dialog.resize(820, 640)

    editor = QPlainTextEdit()
    editor.setPlainText(prompt)
    editor.setReadOnly(True)

    buttons = QDialogButtonBox()
    copy_btn = buttons.addButton(
        "Copy to clipboard", QDialogButtonBox.ButtonRole.ActionRole
    )
    close_btn = buttons.addButton(QDialogButtonBox.StandardButton.Close)
    copy_btn.clicked.connect(lambda: _copy_to_clipboard(editor.toPlainText(), parent))
    close_btn.clicked.connect(dialog.accept)

    layout = QVBoxLayout(dialog)
    layout.addWidget(editor)
    layout.addWidget(buttons)
    dialog.exec()


def _build_guide_text(
    *,
    templates_path: Path,
    template_name: str,
    sample_exam_data: dict | None,
) -> str:
    arch_path = templates_path / "ARCHITECTURE_FOR_AI.md"
    if not arch_path.is_file():
        raise FileNotFoundError(
            f"Architecture file not found: {arch_path}\n"
            "Expected templates/ARCHITECTURE_FOR_AI.md in the project."
        )

    logical_name = normalize_template_name(template_name)
    architecture_text = arch_path.read_text(encoding="utf-8")
    template_source = load_template(templates_path, logical_name)

    sample_context = None
    if sample_exam_data:
        try:
            paper = ExamPaper.model_validate(sample_exam_data)
            sample_context = build_render_context(
                paper, template_name=logical_name
            )
        except Exception:
            sample_context = None

    return build_chatgpt_prompt(
        architecture_text=architecture_text,
        template_name=logical_name,
        template_source=template_source,
        sample_context=sample_context,
    )


def _copy_to_clipboard(text: str, parent) -> None:
    clipboard = QGuiApplication.clipboard()
    clipboard.setText(text)
    QMessageBox.information(parent, "Copied", "Guide copied to clipboard.")
