"""
Pure functional LaTeX transpiler: ExamPaper -> complete document string.

Layout fragments are injected into templates from templates/*.template.tex.
"""

from __future__ import annotations

from pathlib import Path

from core.models import ExamPaper, Question, Section, SubQuestion
from core.template_engine import load_template, render_template, templates_dir

# --- Default preamble fragment (injected into templates) ---
_DOCUMENT_CLASS = r"\documentclass[11pt,a4paper]{article}"
_PACKAGES = r"""\usepackage[margin=2.5cm,top=2.8cm,bottom=2.5cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{array}
\usepackage{tabularx}
\usepackage{enumitem}
\usepackage{parskip}
"""
_PREAMBLE_SPACING = r"""\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.35}
\setlist{nosep,leftmargin=1.4em}
"""
_TITLE_FONT_SIZE = r"\LARGE"
_SUBTITLE_FONT_SIZE = r"\large"
_META_FONT_SIZE = r"\normalsize"
_SECTION_FONT_SIZE = r"\large"
_BODY_FONT_SIZE = r"\normalsize"

_QUESTION_TABLE_SPEC = r"@{}p{1.1cm}X r@{}"
_SUB_QUESTION_TABLE_SPEC = r"@{}p{1.4cm}X r@{}"


def _font_block(font_cmd: str, content: str) -> str:
    """Wrap content so font commands are not merged with text (e.g. \\largeTitle)."""
    return f"{{{font_cmd} {{{content}}}}}"


def build_render_context(paper: ExamPaper) -> dict[str, str]:
    """Build placeholder map for template rendering."""
    return {
        "DOCUMENT_PREAMBLE": "\n".join(
            [_DOCUMENT_CLASS, _PACKAGES, _PREAMBLE_SPACING]
        ),
        "DOCUMENT_HEADER": _render_header(paper),
        "DOCUMENT_BODY": "\n".join(
            _render_section(section) for section in paper.sections
        ),
        "DOCUMENT_FOOTER": "",
    }


def transpile(
    paper: ExamPaper,
    *,
    template_name: str = "default",
    project_root: Path | None = None,
    templates_path: Path | None = None,
) -> str:
    """Render exam paper using the named template file."""
    context = build_render_context(paper)
    if templates_path is None:
        if project_root is None:
            raise ValueError("project_root or templates_path is required")
        templates_path = templates_dir(project_root)
    source = load_template(templates_path, template_name)
    return render_template(source, context)


def _render_header(paper: ExamPaper) -> str:
    lines: list[str] = [
        _BODY_FONT_SIZE,
        r"\begin{center}",
        f"{{{_TITLE_FONT_SIZE}\\textbf{{{paper.title}}}}}",
    ]
    if paper.subtitle:
        lines.append(f"\\\\[4pt]{_font_block(_SUBTITLE_FONT_SIZE, paper.subtitle)}")
    if paper.institution:
        lines.append(f"\\\\[6pt]{_font_block(_META_FONT_SIZE, paper.institution)}")
    meta_parts: list[str] = [
        f"Total Marks: {paper.total_marks}",
        f"(Calculated: {paper.calculated_total_marks})",
    ]
    if paper.duration_minutes is not None:
        meta_parts.append(f"Duration: {paper.duration_minutes} minutes")
    meta_line = " \\quad|\\quad ".join(meta_parts)
    lines.append(f"\\\\[8pt]{_font_block(_META_FONT_SIZE, meta_line)}")
    lines.extend([r"\end{center}", r"\vspace{12pt}", r"\hrule", r"\vspace{14pt}"])
    return "\n".join(lines)


def _render_section(section: Section) -> str:
    lines = [
        f"{{{_SECTION_FONT_SIZE}\\textbf{{Section {section.code}: {section.title}}}}}",
        f"\\hfill\\textbf{{[{section.calculated_marks} marks]}}",
        r"\par\vspace{8pt}",
    ]
    if section.instructions:
        lines.extend(
            [
                r"\textbf{Instructions:} " + section.instructions,
                r"\par\vspace{10pt}",
            ]
        )
    lines.append(
        r"\noindent\begin{tabularx}{\linewidth}{" + _QUESTION_TABLE_SPEC + "}"
    )
    for question in section.questions:
        lines.append(_render_question_row(question))
    lines.extend([r"\end{tabularx}", r"\vspace{18pt}"])
    return "\n".join(lines)


def _render_question_row(question: Question) -> str:
    marks_cell = f"\\textbf{{[{question.marks}]}}"
    row = (
        f"\\textbf{{{question.number}.}} & {question.text} & {marks_cell} \\\\"
    )
    if not question.sub_questions:
        return row
    return "\n".join([row, _render_sub_questions(question.sub_questions)])


def _render_sub_questions(sub_questions: list[SubQuestion]) -> str:
    rows = "\n".join(_render_sub_question_row(sq) for sq in sub_questions)
    return (
        f"\\multicolumn{{3}}{{@{{}}l}}{{%\n"
        f"\\begin{{tabularx}}{{\\linewidth}}{{{_SUB_QUESTION_TABLE_SPEC}}}\n"
        f"{rows}\n"
        f"\\end{{tabularx}}%\n"
        f"}} \\\\"
    )


def _render_sub_question_row(sub: SubQuestion) -> str:
    marks_cell = f"[{sub.marks}]"
    return f"{sub.label} & {sub.text} & {marks_cell} \\\\"
