"""Ejecuta todas las pruebas unitarias desde la raíz del proyecto."""

import os
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> int:
    os.chdir(PROJECT_ROOT)
    suite = unittest.defaultTestLoader.discover(
        "pruebas_unitarias", top_level_dir="."
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
