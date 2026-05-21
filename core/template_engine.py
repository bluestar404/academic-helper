"""Load and render LaTeX templates from the templates/ directory."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

REQUIRED_PLACEHOLDERS = frozenset(
    {
        "DOCUMENT_PREAMBLE",
        "DOCUMENT_HEADER",
        "DOCUMENT_BODY",
    }
)

KNOWN_PLACEHOLDERS = REQUIRED_PLACEHOLDERS | {
    "DOCUMENT_FOOTER",
}


def templates_dir(project_root: Path, configured: str | None = None) -> Path:
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = project_root / path
        return path
    return project_root / "templates"


def normalize_template_name(name: str) -> str:
    """Map UI name to file stem: ``default`` -> ``default``, not ``default.template``."""
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


def validate_template_source(template_source: str) -> list[str]:
    """Return human-readable validation errors (empty list = OK)."""
    errors: list[str] = []
    found = extract_placeholders(template_source)
    missing = REQUIRED_PLACEHOLDERS - found
    if missing:
        errors.append(
            "Missing required placeholders: "
            + ", ".join(f"{{{{{k}}}}}" for k in sorted(missing))
        )
    unknown = found - KNOWN_PLACEHOLDERS
    if unknown:
        errors.append(
            "Unknown placeholders (remove or rename): "
            + ", ".join(f"{{{{{k}}}}}" for k in sorted(unknown))
        )
    if r"\begin{document}" not in template_source:
        errors.append("Template should include \\begin{document}")
    if r"\end{document}" not in template_source:
        errors.append("Template should include \\end{document}")
    return errors


def import_template_file(
    source_file: Path,
    templates_path: Path,
    name: str,
) -> Path:
    """Copy an external .tex file into templates/ as <name>.template.tex."""
    templates_path.mkdir(parents=True, exist_ok=True)
    content = source_file.read_text(encoding="utf-8")
    errors = validate_template_source(content)
    if errors:
        raise ValueError("\n".join(errors))

    dest = template_path(templates_path, name)
    if dest.exists():
        raise FileExistsError(f"Template already exists: {dest.name}")
    shutil.copy2(source_file, dest)
    return dest


def render_template(template_source: str, context: dict[str, str]) -> str:
    """Substitute {{KEY}} placeholders; raises on missing required keys."""
    placeholders = extract_placeholders(template_source)
    missing = REQUIRED_PLACEHOLDERS & placeholders - set(context.keys())
    if missing:
        raise ValueError(f"Template context missing keys: {sorted(missing)}")

    unknown = placeholders - KNOWN_PLACEHOLDERS
    if unknown:
        raise ValueError(f"Template uses unknown placeholders: {sorted(unknown)}")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return context.get(key, "")

    return PLACEHOLDER_PATTERN.sub(replace, template_source)


def build_chatgpt_prompt(
    *,
    architecture_text: str,
    template_name: str,
    template_source: str,
    sample_context: dict[str, str] | None = None,
) -> str:
    """Full prompt to paste into ChatGPT when designing a custom template."""
    placeholders = sorted(extract_placeholders(template_source))
    required = ", ".join(f"{{{{{p}}}}}" for p in sorted(REQUIRED_PLACEHOLDERS))
    optional = "{{DOCUMENT_FOOTER}}"

    sample_block = ""
    if sample_context:
        lines = [
            "=== SAMPLE CONTENT THE APP WILL INJECT (truncated) ===",
            "Do not paste this verbatim into the template; the app generates it.",
        ]
        for key in placeholders:
            value = sample_context.get(key, "")
            preview = value[:600] + ("…" if len(value) > 600 else "")
            lines.append(f"\n--- {key} ({len(value)} chars) ---\n{preview}")
        sample_block = "\n".join(lines)

    return "\n\n".join(
        [
            architecture_text.strip(),
            "=== CURRENT TEMPLATE TO MODIFY ===",
            f"Filename on disk: templates/{template_name}.template.tex",
            "",
            template_source.strip(),
            "",
            "=== PLACEHOLDER CONTRACT ===",
            f"Required (must appear exactly once): {required}",
            f"Optional: {optional}",
            f"Found in file: {', '.join(placeholders)}",
            "",
            sample_block,
            "=== YOUR TASK (ChatGPT) ===",
            "1. Return ONE complete LaTeX file ready to save as "
            f"`{template_name}.template.tex` (or a new name if asked).",
            "2. Keep ALL required {{PLACEHOLDERS}} spelled exactly as shown.",
            "3. Style only the wrapper: fonts, margins, colors, headers/footers, "
            "page size. Do NOT hard-code exam titles or questions.",
            "4. DOCUMENT_BODY already contains every section and question table; "
            "do not duplicate question tables in the template.",
            "5. Ensure the file compiles with Tectonic (pdfLaTeX, utf8 inputenc).",
            "6. Output ONLY the .tex file content — no markdown fences.",
        ]
    )
