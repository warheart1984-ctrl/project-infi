#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface PricingRevenueLayer {
  name: string;
  covers: string[];
}

export interface PricingCustomerSegment {
  name: string;
  buyerMotive: string;
  pricingEmphasis: string;
}

export interface PricingScenarioModel {
  strategy: string;
  packaging: string;
  valueFocus: string;
  marginDriver: string;
}

export interface PricingScenarioMatrixEntry {
  segment: string;
  targetMarginBand: string;
  models: PricingScenarioModel[];
}

export interface PricingModelSpec {
  specId: string;
  displayName: string;
  version: string;
  status: string;
  revenueLayers: PricingRevenueLayer[];
  customerSegments: PricingCustomerSegment[];
  unitEconomics: {
    symbols: Record<string, string>;
  };
  pricingStrategies: string[];
  pricingScenarioMatrix: PricingScenarioMatrixEntry[];
}

function repoRoot(): string {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
}

function releasePath(fileName: string): string {
  return path.join(repoRoot(), 'docs', 'crk1', 'release', fileName);
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isPricingScenarioModel(value: unknown): value is PricingScenarioModel {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const model = value as Partial<PricingScenarioModel>;
  return isString(model.strategy) && isString(model.packaging) && isString(model.valueFocus) && isString(model.marginDriver);
}

function isPricingScenarioMatrixEntry(value: unknown): value is PricingScenarioMatrixEntry {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const entry = value as Partial<PricingScenarioMatrixEntry>;
  return isString(entry.segment) && isString(entry.targetMarginBand) && Array.isArray(entry.models) && entry.models.every(isPricingScenarioModel);
}

function isPricingSpec(value: unknown): value is PricingModelSpec {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const spec = value as Partial<PricingModelSpec>;
  return (
    isString(spec.specId) &&
    isString(spec.displayName) &&
    isString(spec.version) &&
    isString(spec.status) &&
    Array.isArray(spec.revenueLayers) &&
    Array.isArray(spec.customerSegments) &&
    typeof spec.unitEconomics === 'object' &&
    spec.unitEconomics !== null &&
    typeof spec.unitEconomics.symbols === 'object' &&
    spec.unitEconomics.symbols !== null &&
    isStringArray(spec.pricingStrategies) &&
    Array.isArray(spec.pricingScenarioMatrix) &&
    spec.pricingScenarioMatrix.every(isPricingScenarioMatrixEntry)
  );
}

export function loadPricingModelSpec(): PricingModelSpec {
  const raw = JSON.parse(readFileSync(releasePath('SOVEREIGN_ROUTER_X_PRICING.spec.json'), 'utf8')) as unknown;
  if (!isPricingSpec(raw)) {
    throw new Error('SOVEREIGN_ROUTER_X_PRICING.spec.json is malformed');
  }
  return raw;
}

export function summarizePricingModelSpec(spec = loadPricingModelSpec()): {
  revenueLayerCount: number;
  customerSegmentCount: number;
  strategyCount: number;
  scenarioCount: number;
} {
  return {
    revenueLayerCount: spec.revenueLayers.length,
    customerSegmentCount: spec.customerSegments.length,
    strategyCount: spec.pricingStrategies.length,
    scenarioCount: spec.pricingScenarioMatrix.length,
  };
}
