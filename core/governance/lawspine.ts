/**
 * Mythic: Law Spine gate (Runtime Law Spine)
 * Engineering: substrate seal before governed execution.
 * TS consumers use Python RLS at process boot; this module documents the contract.
 */
export const RLS_CONTRACT = {
  engineeringName: "RuntimeLawSpineGate",
  requireSealed: "operator_kernel / aais launcher call ensure_rls_sealed()",
  env: ["RLS_STRICT", "RLS_CONFORMANCE_LEVEL", "UCR_CORRIDOR_REGISTRY", "UCR_LAW_SPINE", "UCR_KERNEL_IMAGE"],
} as const;
