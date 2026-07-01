from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path


PACKAGE_ROOT_NAME = "lawful-nova-shell"

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".runtime",
    ".venv",
    "__pycache__",
    "build",
    "desktop",
    "dist",
    "node_modules",
    "venv",
}

EXCLUDED_SUFFIXES = {
    ".bak",
    ".cmd",
    ".dll",
    ".dylib",
    ".exe",
    ".log",
    ".msi",
    ".pyc",
    ".pyd",
    ".so",
    ".sqlite",
}

EXCLUDED_NAMES = {
    ".env",
    ".env.local",
    ".novarc",
    ".novarc.ps1",
    "nova-audit.log",
}


def create_macos_shell_zip(root: Path, archive: Path) -> Path:
    root = root.resolve()
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in _iter_package_files(root):
            relative = path.relative_to(root).as_posix()
            arcname = f"{PACKAGE_ROOT_NAME}/{relative}"
            info = zipfile.ZipInfo.from_file(path, arcname=arcname)
            mode = _zip_mode(path)
            info.external_attr = (mode & 0xFFFF) << 16
            with path.open("rb") as fh:
                zf.writestr(info, fh.read(), compress_type=zipfile.ZIP_DEFLATED)
    return archive


def _iter_package_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            continue
        if path.is_dir():
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def _zip_mode(path: Path) -> int:
    if _is_shell_executable(path):
        return stat.S_IFREG | 0o755
    return stat.S_IFREG | 0o644


def _is_shell_executable(path: Path) -> bool:
    return path.name == "nova" and path.parent.name == "bin" or path.suffix == ".sh"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the macOS Lawful Nova shell source zip.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    out = args.out or (root / "dist" / "lawful-nova-shell-macos.zip")
    archive = create_macos_shell_zip(root, out)
    print(archive)


if __name__ == "__main__":
    main()
