# LaTeX templates

Each template is one file: **`yourname.template.tex`**

## Add a template (easiest)

1. Run the app → **Add template file…**
2. Pick a `.tex` file (from ChatGPT or your editor)
3. Enter a short name → it is copied here and selected automatically

Or save manually into this folder, then click **Refresh** by reopening the app (or use the dropdown).

## Required content

Your file must include exactly these tokens:

- `{{DOCUMENT_PREAMBLE}}`
- `{{DOCUMENT_HEADER}}`
- `{{DOCUMENT_BODY}}`
- `{{DOCUMENT_FOOTER}}` (may be empty)

Copy [default.template.tex](default.template.tex) as a starting point.

## ChatGPT workflow

1. **AI template guide (copy for ChatGPT)** — copies architecture + your current template + sample data.
2. Paste into ChatGPT; ask for a styled wrapper (not question content).
3. Save the reply → **Add template file…**

Full rules: [ARCHITECTURE_FOR_AI.md](ARCHITECTURE_FOR_AI.md)
