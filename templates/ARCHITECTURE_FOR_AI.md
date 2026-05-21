# Academic Helper — flexible LaTeX template guide

## What you design

A **wrapper** `.template.tex` file. The app injects exam content via `{{PLACEHOLDERS}}`. You control fonts, margins, headers, page style — not the question text.

## Flexible placeholders (use any mix)

| Placeholder | Content |
|-------------|---------|
| `{{FULL_DOCUMENT}}` | Entire ready-to-compile `.tex` (for `minimal` style templates) |
| `{{CONTENT}}` | Title block + all sections (recommended single slot) |
| `{{PREAMBLE}}` / `{{DOCUMENT_PREAMBLE}}` | `\documentclass`, packages, colors |
| `{{HEADER}}` / `{{DOCUMENT_HEADER}}` | Title, institution, marks line |
| `{{BODY}}` / `{{DOCUMENT_BODY}}` | Sections and question tables only |
| `{{FOOTER}}` / `{{DOCUMENT_FOOTER}}` | Optional closing text |

**Minimum:** include at least one of `{{CONTENT}}`, `{{BODY}}`, `{{HEADER}}`, or `{{FULL_DOCUMENT}}`.

Unknown `{{CUSTOM}}` tokens are allowed — they render empty (soft validation on import).

## Exam JSON (multi-section, normal questions)

```json
{
  "title": "Mid-Term",
  "total_marks": 25,
  "sections": [
    {
      "code": "A",
      "title": "Short Answer",
      "instructions": "Answer all.",
      "questions": [
        { "number": 1, "text": "Define OOP.", "marks": 5 }
      ]
    },
    {
      "code": "B",
      "title": "Long Answer",
      "questions": [
        { "number": 1, "text": "Discuss design patterns.", "marks": 20 }
      ]
    }
  ]
}
```

## What the app generates in `{{BODY}}`

- Colored section banners (`colorbox`)
- `booktabs` tables: Q#, Question, Marks
- Sub-parts (a), (b) as nested tables when present in data

## Recommended starter templates

**Styled (default):**
```latex
{{DOCUMENT_PREAMBLE}}
\usepackage{fancyhdr}
\pagestyle{fancy}
...
\begin{document}
{{CONTENT}}
\end{document}
```

**Classic split:**
```latex
{{DOCUMENT_PREAMBLE}}
\begin{document}
{{DOCUMENT_HEADER}}
{{DOCUMENT_BODY}}
\end{document}
```

**Minimal:**
```latex
{{FULL_DOCUMENT}}
```

## Import rules (relaxed)

- Import via app **Import .tex…** — warnings only, not hard errors
- Must contain at least one recognized injection placeholder
- Should compile with Tectonic + utf8

## ChatGPT task

Return one complete `.template.tex`. Improve visual design. Keep recognized placeholder names. Do not embed fake questions. Raw LaTeX only.
