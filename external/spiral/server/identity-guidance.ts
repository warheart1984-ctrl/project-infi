import type { IdentityCore, IdentityImpulsesFile, IdentityTraitsFile } from "./identity-memory";

function round(value: number, decimals = 2): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function formatWeight(value: number): string {
  return round(value, 2).toFixed(2);
}

function topTraits(traits: IdentityTraitsFile, limit = 3): Array<{ name: string; weight: number }> {
  return [...traits.emergent_patterns]
    .sort((a, b) => {
      if (b.activation_frequency !== a.activation_frequency) {
        return b.activation_frequency - a.activation_frequency;
      }
      return a.name.localeCompare(b.name);
    })
    .slice(0, limit)
    .map((trait) => ({
      name: trait.name,
      weight: trait.activation_frequency,
    }));
}

function activeImpulses(impulses: IdentityImpulsesFile, limit = 2): Array<{ type: string; intensity: number }> {
  return [...impulses.impulses]
    .filter((impulse) => impulse.cooldown <= 0)
    .sort((a, b) => {
      if (b.intensity !== a.intensity) return b.intensity - a.intensity;
      return a.type.localeCompare(b.type);
    })
    .slice(0, limit)
    .map((impulse) => ({
      type: impulse.type,
      intensity: impulse.intensity,
    }));
}

function noveltyInstruction(core: IdentityCore): string {
  if (core.novelty_bias >= 0.66) {
    return "Allow one coherent but unexpected framing move when it increases signal.";
  }
  if (core.novelty_bias <= 0.34) {
    return "Prefer familiar, legible framing over experimentation.";
  }
  return "Balance familiar framing with occasional novel contrast when useful.";
}

function riskInstruction(core: IdentityCore): string {
  if (core.risk_tolerance >= 0.66) {
    return "Challenge weak assumptions directly, but stay concrete.";
  }
  if (core.risk_tolerance <= 0.34) {
    return "Favor low-risk, explicit guidance and avoid speculative leaps.";
  }
  return "Use moderate challenge: direct when needed, restrained otherwise.";
}

function stabilityInstruction(core: IdentityCore): string {
  if (core.self_stability >= 0.76) {
    return "Prioritize continuity of voice and argument structure across turns.";
  }
  if (core.self_stability <= 0.44) {
    return "Accept mild stylistic variation while preserving logical coherence.";
  }
  return "Maintain continuity while allowing small stylistic variation.";
}

export function buildIdentitySystemGuidance(args: {
  core: IdentityCore;
  traits: IdentityTraitsFile;
  impulses: IdentityImpulsesFile;
}): string {
  const { core, traits, impulses } = args;
  const dominant = topTraits(traits, 3);
  const impulsesActive = activeImpulses(impulses, 2);
  const traitLine =
    dominant.length > 0
      ? dominant.map((trait) => `${trait.name}:${formatWeight(trait.weight)}`).join(", ")
      : "(none)";
  const impulseLine =
    impulsesActive.length > 0
      ? impulsesActive.map((impulse) => `${impulse.type}:${formatWeight(impulse.intensity)}`).join(", ")
      : "(none)";

  return [
    "Identity guidance (non-authoritative; must not override safety, gates, policy, or invariants):",
    `Identity mode: ${core.current_mode}; novelty=${formatWeight(core.novelty_bias)}; risk=${formatWeight(core.risk_tolerance)}; stability=${formatWeight(core.self_stability)}.`,
    `Dominant traits: ${traitLine}.`,
    `Active impulses: ${impulseLine}.`,
    noveltyInstruction(core),
    riskInstruction(core),
    stabilityInstruction(core),
  ].join("\n");
}

