"""Flexible LaTeX template loading and placeholder rendering."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# Canonical keys the app always supplies
STANDARD_KEYS = frozenset(
    {
        "DOCUMENT_PREAMBLE",
        "DOCUMENT_HEADER",
        "DOCUMENT_BODY",
        "DOCUMENT_FOOTER",
        "CONTENT",
        "PREAMBLE",
        "HEADER",
        "BODY",
        "FOOTER",
        "FULL_DOCUMENT",
    }
)

# At least one of these must appear in a template
INJECTION_POINTS = frozenset(
    {
        "FULL_DOCUMENT",
        "CONTENT",
        "DOCUMENT_BODY",
        "BODY",
        "DOCUMENT_HEADER",
        "HEADER",
    }
)


def templates_dir(project_root: Path, configured: str | None = None) -> Path:
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = project_root / path
        return path
    return project_root / "templates"


def normalize_template_name(name: str) -> str:
    logical = name.strip()
    if logical.endswith(".template.tex"):
        logical = logical[: -len(".template.tex")]
    elif logical.endswith(".template"):
        logical = logical[: -len(".template")]
    return re.sub(r"[^\w\-]", "_", logical)


def list_templates(templates_path: Path) -> list[str]:
    templates_path.mkdir(parents=True, exist_ok=True)
    names = sorted(
        path.name[: -len(".template.tex")]
        for path in templates_path.glob("*.template.tex")
        if path.is_file()
    )
    return names or ["default"]


def template_path(templates_path: Path, name: str) -> Path:
    safe = normalize_template_name(name)
    return templates_path / f"{safe}.template.tex"


def load_template(templates_path: Path, name: str) -> str:
    path = template_path(templates_path, name)
    if not path.is_file():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def extract_placeholders(template_source: str) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(template_source))


def expand_context(context: dict[str, str]) -> dict[str, str]:
    """Add aliases so templates can use short or long placeholder names."""
    preamble = context.get("DOCUMENT_PREAMBLE", "")
    header = context.get("DOCUMENT_HEADER", "")
    body = context.get("DOCUMENT_BODY", "")
    footer = context.get("DOCUMENT_FOOTER", "")
    content = context.get("CONTENT", f"{header}\n{body}\n{footer}".strip())

    full_document = context.get(
        "FULL_DOCUMENT",
        "\n".join(
            [
                preamble,
                r"\begin{document}",
                content,
                r"\end{document}",
            ]
        ).strip(),
    )

    expanded = dict(context)
    expanded.update(
        {
            "DOCUMENT_PREAMBLE": preamble,
            "DOCUMENT_HEADER": header,
            "DOCUMENT_BODY": body,
            "DOCUMENT_FOOTER": footer,
            "CONTENT": content,
            "PREAMBLE": preamble,
            "HEADER": header,
            "BODY": body,
            "FOOTER": footer,
            "FULL_DOCUMENT": full_document,
        }
    )
    return expanded


def validate_template_source(template_source: str, *, strict: bool = False) -> list[str]:
    """Return warnings/errors. Non-strict mode allows flexible templates."""
    issues: list[str] = []
    found = extract_placeholders(template_source)

    if not found:
        issues.append("No {{PLACEHOLDERS}} found — add at least {{CONTENT}} or {{BODY}}.")
        return issues

    if not found & INJECTION_POINTS:
        issues.append(
            "Add an injection point: {{CONTENT}}, {{BODY}}, {{HEADER}}, or {{FULL_DOCUMENT}}."
        )

    unknown = found - STANDARD_KEYS
    if unknown:
        msg = (
            "Optional custom placeholders (will be left blank unless you add them to the app): "
            + ", ".join(sorted(unknown))
        )
        if strict:
            issues.append(msg)
        else:
            issues.append(f"(notice) {msg}")

    if strict:
        if r"\begin{document}" not in template_source and "FULL_DOCUMENT" not in found:
            issues.append("Include \\begin{document} or use {{FULL_DOCUMENT}} only.")
        if r"\end{document}" not in template_source and "FULL_DOCUMENT" not in found:
            issues.append("Include \\end{document} or use {{FULL_DOCUMENT}} only.")

    return issues


def render_template(
    template_source: str,
    context: dict[str, str],
    *,
    strict: bool = False,
) -> str:
    """Substitute placeholders; unknown tokens become empty unless strict."""
    expanded = expand_context(context)
    placeholders = extract_placeholders(template_source)

    if strict:
        missing = (placeholders & STANDARD_KEYS) - set(expanded.keys())
        if missing:
            raise ValueError(f"Template context missing keys: {sorted(missing)}")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in expanded:
            return expanded[key]
        if key in STANDARD_KEYS:
            return ""
        return ""  # custom placeholder — empty

    result = PLACEHOLDER_PATTERN.sub(replace, template_source)

    if "FULL_DOCUMENT" in placeholders and placeholders == {"FULL_DOCUMENT"}:
        return expanded["FULL_DOCUMENT"]

    return result


def import_template_file(
    source_file: Path,
    templates_path: Path,
    name: str,
    *,
    strict: bool = False,
) -> Path:
    templates_path.mkdir(parents=True, exist_ok=True)
    content = source_file.read_text(encoding="utf-8")
    errors = validate_template_source(content, strict=strict)
    blocking = [e for e in errors if not e.startswith("(notice)")]
    if blocking and strict:
        raise ValueError("\n".join(blocking))

    dest = template_path(templates_path, name)
    if dest.exists():
        raise FileExistsError(f"Template already exists: {dest.name}")
    shutil.copy2(source_file, dest)
    return dest


def build_chatgpt_prompt(
    *,
    architecture_text: str,
    template_name: str,
    template_source: str,
    sample_context: dict[str, str] | None = None,
) -> str:
    placeholders = sorted(extract_placeholders(template_source))

    sample_block = ""
    if sample_context:
        expanded = expand_context(sample_context)
        lines = ["=== SAMPLE INJECTED FRAGMENTS (truncated) ==="]
        for key in placeholders:
            if key not in expanded:
                continue
            value = expanded[key]
            preview = value[:500] + ("…" if len(value) > 500 else "")
            lines.append(f"\n--- {{{{{key}}}}} ---\n{preview}")
        sample_block = "\n".join(lines)

    return "\n\n".join(
        [
            architecture_text.strip(),
            "=== CURRENT TEMPLATE ===",
            f"File: templates/{template_name}.template.tex",
            "",
            template_source.strip(),
            "",
            "=== FLEXIBLE PLACEHOLDERS (use any combination) ===",
            "{{FULL_DOCUMENT}} — entire .tex (for pass-through wrappers)",
            "{{CONTENT}} — header + all sections (most common body slot)",
            "{{PREAMBLE}} / {{DOCUMENT_PREAMBLE}} — packages & layout setup",
            "{{HEADER}} / {{DOCUMENT_HEADER}} — title block only",
            "{{BODY}} / {{DOCUMENT_BODY}} — sections & questions only",
            "{{FOOTER}} / {{DOCUMENT_FOOTER}} — closing block",
            "",
            f"Detected in file: {', '.join(placeholders) or '(none)'}",
            sample_block,
            "=== TASK ===",
            "Return a complete .template.tex file. Improve visual design (fonts, margins, "
            "headers, section styling). Keep placeholder names the app recognizes. "
            "Do NOT hard-code exam questions. Output raw LaTeX only.",
        ]
    )
