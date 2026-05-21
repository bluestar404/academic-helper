"""SPPU (Pune University) examination paper LaTeX layout."""

from __future__ import annotations

from core.models import ExamPaper, Question, Section, SubQuestion

_SPPU_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2cm,top=2cm,bottom=2cm,left=2.2cm,right=2.2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{times}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{amsmath}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
"""

_OR_BLOCK = (
    r"\vspace{10pt}"
    r"\begin{center}\textbf{OR}\end{center}"
    r"\vspace{10pt}"
)


def _total_question_count(paper: ExamPaper) -> int:
    return sum(len(s.questions) for s in paper.sections)


def _format_time(paper: ExamPaper) -> str:
    if paper.time_display:
        return paper.time_display
    if paper.duration_minutes:
        hours = paper.duration_minutes // 60
        mins = paper.duration_minutes % 60
        if mins == 0:
            return f"{hours} Hour{'s' if hours != 1 else ''}"
        if hours:
            return f"{hours} {'Hour' if hours == 1 else 'Hours'} {mins} min"
        return f"{paper.duration_minutes} min"
    return "2 1/2 Hours"


def render_sppu_preamble() -> str:
    return _SPPU_PREAMBLE


def render_sppu_header(paper: ExamPaper) -> str:
    paper_code = paper.paper_code or "P3556"
    exam_code = paper.exam_code or "[4959] - 1156"
    course = paper.subtitle or "B.E. (Computer Engg.) (Semester - I)"
    subject = paper.title
    pattern = paper.institution or "(2012 Pattern) (Elective - I)"
    time_text = _format_time(paper)
    total_q = _total_question_count(paper)

    return "\n".join(
        [
            r"\noindent\begin{minipage}[t]{0.52\linewidth}",
            f"Total No. of Questions : {total_q}\\\\",
            paper_code,
            r"\end{minipage}%",
            r"\hfill\begin{minipage}[t]{0.42\linewidth}\raggedleft",
            r"\textbf{SEAT No. : }\fbox{\rule{0pt}{0.75cm}\rule{1.7cm}{0pt}}\\[4pt]",
            r"[Total No. of Pages : 3]",
            r"\end{minipage}",
            r"\vspace{8pt}",
            r"\begin{center}",
            f"\\textbf{{{exam_code}}}\\\\[6pt]",
            f"\\textbf{{{course}}}\\\\[4pt]",
            f"\\textbf{{{subject}}}\\\\[4pt]",
            f"\\textbf{{{pattern}}}",
            r"\end{center}",
            r"\vspace{10pt}",
            r"\noindent\begin{tabularx}{\linewidth}{@{}X r@{}}",
            f"\\textbf{{Time : {time_text}}} & "
            f"\\textbf{{[Max. Marks : {paper.total_marks}]}} \\\\",
            r"\end{tabularx}",
            r"\vspace{12pt}",
        ]
    )


def render_sppu_instructions(section: Section) -> str:
    if not section.instructions:
        return ""
    parts = [p.strip() for p in section.instructions.split(";") if p.strip()]
    if not parts:
        parts = [section.instructions.strip()]
    lines = [
        r"\textbf{Instructions to the candidates:}",
        r"\begin{enumerate}[leftmargin=*, itemsep=2pt]",
        *[f"\\item {part}" for part in parts],
        r"\end{enumerate}",
        r"\vspace{10pt}",
    ]
    return "\n".join(lines)


def _part_line(label: str, text: str, marks: int) -> str:
    prefix = f"{label} " if label else ""
    return (
        f"\\noindent {prefix}{text}"
        f"\\hfill\\textbf{{[{marks}]}}"
        "\\\\"
    )


def _render_sppu_question(question: Question) -> str:
    if question.sub_questions:
        lines = [f"\\noindent\\textbf{{Q{question.number})}}"]
        for sq in question.sub_questions:
            label = sq.label if sq.label.endswith(")") else f"{sq.label})"
            lines.append(_part_line(label, sq.text, sq.marks))
        return "\n".join(lines)
    return (
        f"\\noindent\\textbf{{Q{question.number})}} "
        f"{question.text}\\hfill\\textbf{{[{question.marks}]}} "
        "\\\\"
    )


def render_sppu_body(paper: ExamPaper) -> str:
    blocks: list[str] = []
    for section in paper.sections:
        if len(paper.sections) > 1:
            blocks.append(
                f"\\textbf{{Section {section.code}: {section.title}}}"
                r"\\[6pt]"
            )
        blocks.append(render_sppu_instructions(section))
        for i, question in enumerate(section.questions):
            blocks.append(_render_sppu_question(question))
            if i < len(section.questions) - 1:
                blocks.append(_OR_BLOCK)
    return "\n\n".join(blocks)


def render_sppu_content(paper: ExamPaper) -> str:
    return "\n\n".join(
        [
            render_sppu_header(paper),
            render_sppu_body(paper),
        ]
    )
