# Academic Helper — template contract for AI assistants

Paste this document together with your current `.template.tex` (use the app's **AI template guide** button). The goal is a **wrapper LaTeX file** the desktop app fills with exam content.

---

## What this app is

Academic Helper is a **question paper generator** (not a quiz/MCQ app). Teachers enter:

- Exam metadata (title, college, duration, total marks)
- **Multiple sections** (e.g. Section A, Section B), each with optional instructions
- **Normal written questions** with marks (and optional sub-parts (a), (b) in data — usually entered as separate rows)

The app validates JSON-like data, escapes LaTeX-special characters in user text, builds three LaTeX fragments, injects them into **your** template, and compiles PDF with **Tectonic**.

---

## Files you may edit

| File | Purpose |
|------|---------|
| `templates/<name>.template.tex` | **You design this** — layout shell only |
| `templates/ARCHITECTURE_FOR_AI.md` | This instruction file |
| `templates/default.template.tex` | Minimal working example |

The app **never** stores questions inside the template file.

---

## Required placeholder tokens

Use **exact** names (double curly braces, ALL CAPS):

| Token | Filled by app | Typical contents |
|-------|----------------|------------------|
| `{{DOCUMENT_PREAMBLE}}` | App | `\documentclass`, `\usepackage{...}`, spacing |
| `{{DOCUMENT_HEADER}}` | App | Centered title, subtitle, institution, marks, duration |
| `{{DOCUMENT_BODY}}` | App | **All sections** — each section heading + question `tabularx` |
| `{{DOCUMENT_FOOTER}}` | App | Usually empty string; optional end matter |

**Rules**

1. Keep `\begin{document}` … `\end{document}` in the template (see default).
2. Do **not** rename placeholders — the app errors if any required token is missing.
3. Do **not** add extra `{{CUSTOM}}` tokens — only the four above are supported.
4. User question text in `DOCUMENT_BODY` is **already escaped** (`\%`, `\&`, `\$`, `\_`). Static text in your template must use `\&` not `&`.

---

## Exam JSON the app produces

```json
{
  "title": "Mid-Term Examination",
  "subtitle": "Computer Science II",
  "institution": "Example College",
  "duration_minutes": 90,
  "total_marks": 25,
  "sections": [
    {
      "code": "A",
      "title": "Short Answer",
      "instructions": "Answer all questions.",
      "questions": [
        { "number": 1, "text": "Define polymorphism.", "marks": 5 },
        { "number": 2, "text": "Explain inheritance with an example.", "marks": 10 }
      ]
    },
    {
      "code": "B",
      "title": "Long Answer",
      "instructions": "Attempt any two.",
      "questions": [
        { "number": 1, "text": "Discuss REST API design.", "marks": 10 }
      ]
    }
  ]
}
```

**Validation**

- `total_marks` = sum of all question marks in all sections.
- Section `code` values must be unique (e.g. `A`, `B`).
- Question `number` unique **within** each section.
- Optional `sub_questions` on a question: parent `marks` must equal sum of sub-part marks (advanced; UI may use separate rows).

There is **no** `options` field — this is not multiple-choice.

---

## What `DOCUMENT_BODY` looks like (generated — do not copy into template)

The app emits one block per section, roughly:

```latex
{\large\textbf{Section A: Short Answer}}
\hfill\textbf{[15 marks]}
\par\vspace{8pt}
\textbf{Instructions:} Answer all questions.
\par\vspace{10pt}
\noindent\begin{tabularx}{\linewidth}{@{}p{1.1cm}X r@{}}
\textbf{1.} & Define polymorphism. & \textbf{[5]} \\
\textbf{2.} & Explain inheritance with an example. & \textbf{[10]} \\
\end{tabularx}
\vspace{18pt}
```

Then Section B, etc. Your template should **not** add a second question table — only wrap `{{DOCUMENT_BODY}}`.

`DOCUMENT_PREAMBLE` already includes `\usepackage{tabularx}` and related packages.

---

## Minimal valid template (copy-paste baseline)

```latex
{{DOCUMENT_PREAMBLE}}
\begin{document}
{{DOCUMENT_HEADER}}
{{DOCUMENT_BODY}}
{{DOCUMENT_FOOTER}}
\end{document}
```

---

## What you MAY customize

- Page size, margins (`geometry`), fonts (`lmodern`, `mathptmx`, etc.)
- Colors, rules, fancy headers/footers (`fancyhdr`)
- Wrapping `DOCUMENT_HEADER` in a box or minipage
- Adding static text **outside** placeholders (e.g. "Confidential")

## What you must NOT do

- Remove or rename `{{DOCUMENT_PREAMBLE}}`, `{{DOCUMENT_HEADER}}`, `{{DOCUMENT_BODY}}`
- Put sample questions or `\begin{tabularx}` for exam content in the template
- Expect raw `%` or `&` from users inside `DOCUMENT_BODY` (already escaped)

---

## After ChatGPT returns your file

1. Save as `templates/mytheme.template.tex` **or** use the app button **Add template file…** to import it.
2. Select **mytheme** in the template dropdown.
3. Click **Generate PDF**.

---

## Quick checklist

- [ ] All three required placeholders present
- [ ] `\begin{document}` and `\end{document}` present
- [ ] No extra `{{PLACEHOLDERS}}`
- [ ] Compiles with Tectonic when filled with sample content
- [ ] No duplicate question tables outside `{{DOCUMENT_BODY}}`
