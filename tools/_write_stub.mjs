import fs from "node:fs";
import path from "node:path";
const root = path.resolve(".");
const files = new Map();
// populated by append calls below
