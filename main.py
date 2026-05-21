"""
Module C: Application entry point — PySide6 lifecycle, config, safe UI startup.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication, QMessageBox

from app_window import AppWindow
from core.compiler import resolve_tectonic
from core.template_engine import templates_dir

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG: dict[str, Any] = {
    "window_title": "Academic Helper",
    "tectonic_path": "vendor/tectonic.exe",
    "output_dir": "output",
    "templates_dir": "templates",
    "default_template": "default",
}


def load_config() -> dict[str, Any]:
    config_path = PROJECT_ROOT / "config.json"
    config = dict(DEFAULT_CONFIG)
    if config_path.is_file():
        with config_path.open(encoding="utf-8") as fh:
            config.update(json.load(fh))

    config["project_root"] = str(PROJECT_ROOT)

    tectonic = resolve_tectonic(
        PROJECT_ROOT,
        configured=config.get("tectonic_path"),
    )
    config["tectonic_path"] = str(tectonic)

    output_dir = Path(config["output_dir"])
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    config["output_dir"] = str(output_dir)

    tpl_dir = templates_dir(PROJECT_ROOT, config.get("templates_dir"))
    config["templates_dir"] = str(tpl_dir)

    return config


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Academic Helper")

    try:
        config = load_config()
    except FileNotFoundError as exc:
        QMessageBox.critical(None, "Configuration error", str(exc))
        return 1

    window = AppWindow(config)
    window.setWindowTitle(config.get("window_title", DEFAULT_CONFIG["window_title"]))
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
