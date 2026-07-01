import fs from "node:fs";
import { COR_SUITE_PATHS } from "../paths.js";
import type { CarRegistry } from "../types/car.js";
import { readJsonInput, writeJsonOutput } from "../lib/io.js";

export function loadCarRegistry(): CarRegistry {
  return readJsonInput<CarRegistry>(COR_SUITE_PATHS.carRegistry);
}

export function saveCarRegistry(registry: CarRegistry): string {
  fs.mkdirSync(COR_SUITE_PATHS.carDir, { recursive: true });
  return writeJsonOutput(COR_SUITE_PATHS.carRegistry, registry);
}

export function carRegistryExists(): boolean {
  return fs.existsSync(COR_SUITE_PATHS.carRegistry);
}
