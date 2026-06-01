import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const TARGET_FILES = [
  "../server/veil-channel.mirror.ts",
] as const;

const BANNED_LABEL_WORDS = /\b(?:internal|recall|memory|contracts?|thread|state)\b/i;

function extractShapeUtteranceBlock(source: string): string {
  const start = source.indexOf("function shapeUtterance(");
  assert.notEqual(start, -1, "Expected shapeUtterance function to exist.");

  const nextFunction = source.indexOf("\nfunction ", start + 1);
  assert.notEqual(nextFunction, -1, "Expected another function after shapeUtterance.");

  return source.slice(start, nextFunction);
}

function extractStringLiterals(source: string): string[] {
  const literals: string[] = [];
  const literalPattern = /(["'`])((?:\\.|(?!\1)[\s\S])*?)\1/g;
  let match: RegExpExecArray | null = null;

  while ((match = literalPattern.exec(source)) !== null) {
    const quote = match[1];
    const raw = match[2] || "";
    const normalized =
      quote === "`"
        ? raw.replace(/\$\{[^}]*\}/g, " ").trim()
        : raw.trim();
    if (normalized.length > 0) {
      literals.push(normalized);
    }
  }

  return literals;
}

test("shapeUtterance keeps recall controls non-narratable", async () => {
  for (const relativePath of TARGET_FILES) {
    const fileUrl = new URL(relativePath, import.meta.url);
    const source = await readFile(fileUrl, "utf8");
    const shapeBlock = extractShapeUtteranceBlock(source);
    const literals = extractStringLiterals(shapeBlock);
    const violations = literals.filter((literal) => BANNED_LABEL_WORDS.test(literal));

    assert.deepEqual(
      violations,
      [],
      `${relativePath} shapeUtterance contains banned narratable labels: ${violations.join(" | ")}`,
    );
  }
});
