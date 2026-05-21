"""
LaTeX transpiler: ExamPaper -> fragments for flexible templates.
"""

from __future__ import annotations

from pathlib import Path

from core.models import ExamPaper, Question, Section, SubQuestion
from core.sppu_layout import (
    render_sppu_content,
    render_sppu_preamble,
)
from core.template_engine import expand_context, load_template, render_template, templates_dir

SPPU_TEMPLATE = "sppu_original"

_DOCUMENT_CLASS = r"\documentclass[11pt,a4paper]{article}"
_PACKAGES = r"""\usepackage[margin=2cm,top=2.2cm,bottom=2.2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{array}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{parskip}
\usepackage{tikz}
"""
_PREAMBLE_SPACING = r"""\definecolor{examblue}{RGB}{25,55,109}
\definecolor{examrule}{RGB}{180,190,210}
\definecolor{examlight}{RGB}{245,247,252}
\setlength{\parskip}{7pt}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.4}
\setlist{nosep,leftmargin=1.5em}
"""
_QUESTION_TABLE_SPEC = r"@{}>{\bfseries}p{1.2cm}X>{\raggedleft\arraybackslash}p{1.5cm}@{}"
_SUB_QUESTION_TABLE_SPEC = r"@{}p{1.5cm}X r@{}"


def _font_block(font_cmd: str, content: str) -> str:
    return f"{{{font_cmd} {{{content}}}}}"


def build_render_context(
    paper: ExamPaper,
    *,
    template_name: str = "default",
) -> dict[str, str]:
    if normalize_template_name(template_name) == SPPU_TEMPLATE:
        content = render_sppu_content(paper)
        base = {
            "DOCUMENT_PREAMBLE": render_sppu_preamble(),
            "DOCUMENT_HEADER": "",
            "DOCUMENT_BODY": content,
            "DOCUMENT_FOOTER": "",
            "CONTENT": content,
        }
        return expand_context(base)

    header = _render_header(paper)
    body = "\n".join(_render_section(section) for section in paper.sections)
    footer = ""
    preamble = "\n".join([_DOCUMENT_CLASS, _PACKAGES, _PREAMBLE_SPACING])
    content = "\n\n".join(part for part in (header, body, footer) if part)

    base = {
        "DOCUMENT_PREAMBLE": preamble,
        "DOCUMENT_HEADER": header,
        "DOCUMENT_BODY": body,
        "DOCUMENT_FOOTER": footer,
        "CONTENT": content,
    }
    return expand_context(base)


def normalize_template_name(name: str) -> str:
    from core.template_engine import normalize_template_name as _norm

    return _norm(name)


def transpile(
    paper: ExamPaper,
    *,
    template_name: str = "default",
    project_root: Path | None = None,
    templates_path: Path | None = None,
) -> str:
    context = build_render_context(paper, template_name=template_name)
    if templates_path is None:
        if project_root is None:
            raise ValueError("project_root or templates_path is required")
        templates_path = templates_dir(project_root)
    source = load_template(templates_path, template_name)
    return render_template(source, context, strict=False)


def _render_header(paper: ExamPaper) -> str:
    meta_parts: list[str] = [f"Total marks: {paper.total_marks}"]
    if paper.duration_minutes is not None:
        meta_parts.append(f"Duration: {paper.duration_minutes} min")
    meta_line = r" \textbullet\ ".join(meta_parts)

    lines = [
        r"\begin{center}",
        r"\begin{tikzpicture}",
        r"\node[fill=examlight, rounded corners=4pt, inner sep=14pt, text width=0.92\linewidth] (box) {",
        f"{{\\fontsize{{18}}{{22}}\selectfont\\textcolor{{examblue}}{{\\textbf{{{paper.title}}}}}}}",
    ]
    if paper.subtitle:
        lines.append(
            f"\\\\[6pt]{{\\large\\textcolor{{examblue}}{{{paper.subtitle}}}}}"
        )
    if paper.institution:
        lines.append(f"\\\\[4pt]{{\\normalsize {paper.institution}}}")
    lines.append(f"\\\\[8pt]{{\\small {meta_line}}}")
    lines.extend([r"};", r"\end{tikzpicture}", r"\end{center}", r"\vspace{10pt}"])
    return "\n".join(lines)


def _render_section(section: Section) -> str:
    lines = [
        r"\vspace{6pt}",
        r"\noindent\colorbox{examlight}{%",
        r"\begin{minipage}{\dimexpr\linewidth-2\fboxsep}",
        f"\\textcolor{{examblue}}{{\\large\\textbf{{Section {section.code}: {section.title}}}}}"
        f"\\hfill\\textbf{{[{section.calculated_marks} marks]}}",
        r"\end{minipage}%",
        r"}",
        r"\vspace{8pt}",
    ]
    if section.instructions:
        lines.extend(
            [
                r"\textit{\textbf{Instructions:}} " + section.instructions,
                r"\par\vspace{8pt}",
            ]
        )
    lines.extend(
        [
            r"\noindent\begin{tabularx}{\linewidth}{" + _QUESTION_TABLE_SPEC + "}",
            r"\toprule",
            r"\textbf{Q\#} & \textbf{Question} & \textbf{Marks} \\",
            r"\midrule",
        ]
    )
    for i, question in enumerate(section.questions):
        lines.append(_render_question_row(question))
        if i < len(section.questions) - 1:
            lines.append(r"\addlinespace[3pt]")
    lines.extend([r"\bottomrule", r"\end{tabularx}", r"\vspace{16pt}"])
    return "\n".join(lines)


def _render_question_row(question: Question) -> str:
    marks_cell = f"\\textbf{{{question.marks}}}"
    row = f"{question.number}. & {question.text} & {marks_cell} \\\\"
    if not question.sub_questions:
        return row
    return "\n".join([row, _render_sub_questions(question.sub_questions)])


def _render_sub_questions(sub_questions: list[SubQuestion]) -> str:
    rows = "\n".join(_render_sub_question_row(sq) for sq in sub_questions)
    return (
        f"\\multicolumn{{3}}{{@{{}}l}}{{%\n"
        f"\\hspace{{1.2cm}}\\begin{{tabularx}}{{\\dimexpr\\linewidth-1.2cm}}{{{_SUB_QUESTION_TABLE_SPEC}}}\n"
        f"{rows}\n"
        f"\\end{{tabularx}}%\n"
        f"}} \\\\"
    )


def _render_sub_question_row(sub: SubQuestion) -> str:
    return f"{sub.label} & {sub.text} & {sub.marks} \\\\"
