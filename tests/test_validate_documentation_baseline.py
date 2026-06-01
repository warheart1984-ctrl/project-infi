from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / ".github" / "scripts" / "validate-documentation-baseline.py"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_documentation_baseline", VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator_module()


class ValidateDocumentationBaselineTests(unittest.TestCase):
    def test_repo_readme_passes_ma12(self) -> None:
        findings, errors = validator._validate_operational_primer(REPO_ROOT / "README.md")
        self.assertFalse(errors, msg="\n".join(f.render() for f in findings))

    def test_missing_readme_fails(self) -> None:
        _, errors = validator._validate_operational_primer(REPO_ROOT / "missing-readme.md")
        self.assertTrue(errors)

    def test_missing_operations_section_fails(self) -> None:
        readme = REPO_ROOT / "tmp" / "ma12-test-readme.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text("# Demo\n\nNo operations section.\n", encoding="utf-8")
        try:
            _, errors = validator._validate_operational_primer(readme)
            self.assertTrue(errors)
        finally:
            readme.unlink(missing_ok=True)

    def test_lawbook_contains_ma12(self) -> None:
        findings, errors = validator._validate_meta_lawbook(REPO_ROOT)
        self.assertFalse(errors, msg="\n".join(f.render() for f in findings))


if __name__ == "__main__":
    unittest.main()
