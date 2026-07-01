#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Generate .tex sections from markdown if pandoc is available
if command -v pandoc >/dev/null 2>&1; then
  for md in ../../src/sections/*.md; do
  base=$(basename "$md" .md)
  pandoc "$md" -f markdown -t latex -o "../../src/sections/${base}.tex"
  done
fi

latexmk -pdf wolf1_v1.1.tex
