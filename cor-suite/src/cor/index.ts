import { COR_SUITE_PATHS } from "../paths.js";
import type { CorStateVector } from "../types/cor.js";
import { writeJsonOutput } from "../lib/io.js";
import { loadCarRegistry, carRegistryExists } from "../car/registry.js";
import { emitCavValidation, cavPasses, validateCarRegistry } from "../car/validate.js";
import { buildCorStateFromCar } from "./from-car.js";

export async function generateCorState(): Promise<CorStateVector> {
  if (!carRegistryExists()) {
    throw new Error(
      `CAR registry missing at ${COR_SUITE_PATHS.carRegistry} — run: npm run car:bootstrap`,
    );
  }

  const car = loadCarRegistry();
  const cav = validateCarRegistry(car);
  if (!cavPasses(cav)) {
    throw new Error(
      `CAV-1.0 validation failed (${cav.blockingCount} blocking) — run: npm run validate`,
    );
  }

  return buildCorStateFromCar(car);
}

export async function emitCorState(): Promise<string> {
  const cor = await generateCorState();
  return writeJsonOutput(COR_SUITE_PATHS.outputs.corState, {
    ...cor,
    carRef: COR_SUITE_PATHS.carRegistry,
  });
}

/** Validate CAR and emit CAV report without building COR. */
export function validateAndEmitCav(): { valid: boolean; path: string } {
  const result = emitCavValidation();
  return { valid: cavPasses(result), path: COR_SUITE_PATHS.outputs.cavValidation };
}
