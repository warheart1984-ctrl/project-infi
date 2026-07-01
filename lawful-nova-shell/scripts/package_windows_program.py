from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path


PACKAGE_ROOT_NAME = "nova-desktop-windows"

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".runtime",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

EXCLUDED_SUFFIXES = {
    ".bak",
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


def create_windows_program_zip(root: Path, archive: Path) -> Path:
    root = root.resolve()
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in _iter_package_files(root):
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo.from_file(path, arcname=f"{PACKAGE_ROOT_NAME}/{relative}")
            info.external_attr = (_zip_mode(path) & 0xFFFF) << 16
            with path.open("rb") as fh:
                zf.writestr(info, fh.read(), compress_type=zipfile.ZIP_DEFLATED)
    return archive


def _iter_package_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if _is_excluded_dir(relative_parts):
            continue
        if path.is_dir():
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def _is_excluded_dir(parts: tuple[str, ...]) -> bool:
    for index, part in enumerate(parts):
        if part in EXCLUDED_DIRS:
            if part == "dist" and index > 0 and parts[index - 1] == "desktop":
                return True
            if part == "build" and index > 0 and parts[index - 1] == "desktop":
                return True
            if part in {"dist", "build"} and index == 0:
                return True
            return True
    return False


def _zip_mode(path: Path) -> int:
    if path.name.endswith(".ps1") or path.name.endswith(".cmd") or path.name.endswith(".bat"):
        return stat.S_IFREG | 0o644
    if path.suffix == ".sh" or (path.name == "nova" and path.parent.name == "bin"):
        return stat.S_IFREG | 0o755
    return stat.S_IFREG | 0o644


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the Windows Nova Desktop source zip.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    out = args.out or (root / "dist" / "nova-desktop-windows.zip")
    archive = create_windows_program_zip(root, out)
    print(archive)


if __name__ == "__main__":
    main()
