/**
 * CAR-1.0 public API — load, save, register canonical artifacts.
 */
import type { CarArtifact, CarRegistry } from "../types/car.js";
import {
  carRegistryExists,
  loadCarRegistry,
  saveCarRegistry,
} from "./registry.js";

export { carRegistryExists, bootstrapCarRegistry } from "./bootstrap.js";
export type { CarArtifact, CarRegistry } from "../types/car.js";

export function loadCar(): CarRegistry {
  return loadCarRegistry();
}

export function saveCar(car: CarRegistry): string {
  car.generatedAt = new Date().toISOString();
  return saveCarRegistry(car);
}

export function registerArtifact(entry: CarArtifact): string {
  const car = loadCar();
  if (car.artifacts.some((a) => a.id === entry.id)) {
    throw new Error(`Duplicate CAR artifact id: ${entry.id}`);
  }
  car.artifacts.push(entry);
  return saveCar(car);
}
