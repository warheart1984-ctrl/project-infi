export const COMPOSE_MODE_LABELS = {
  fast: 'Fast',
  small: 'Small Nova',
  tiny: 'Tiny Nova',
  governed_full: 'Governed full',
  deep: 'Deep compose',
};

export function normalizeComposeReceipt(payload = {}) {
  const receipt = payload.compose_receipt || payload.composeReceipt || payload.receipt || null;
  if (!receipt) {
    return null;
  }
  return {
    status: receipt.status || 'ok',
    composeMode: receipt.compose_mode || receipt.composeMode || payload.response_mode || 'fast',
    composeModeLabel: receipt.compose_mode_label || receipt.composeModeLabel,
    arisStatus: receipt.aris_status || receipt.arisStatus || 'ready',
    novaFaceId: receipt.nova_face_id || receipt.novaFaceId || '',
    composeMs: receipt.compose_ms ?? receipt.composeMs ?? null,
    hasCoherenceProjection: Boolean(receipt.has_coherence_projection ?? receipt.hasCoherenceProjection),
    spineDoctrine: receipt.spine_doctrine || receipt.spineDoctrine || '',
    activeRuntimes: receipt.active_runtimes || receipt.activeRuntimes || [],
    reasonCodes: receipt.reason_codes || receipt.reasonCodes || [],
  };
}

export function summarizeSuperNovaCompose(payload = {}) {
  const source = payload || {};
  const state = source.super_nova || source.superNova || source.super_nova_state || {};
  return {
    activationState: state.activation_state || state.activationState || 'inactive',
    phaseDecision: state.phase_decision || state.phaseDecision || 'not_required',
    tokenPresent: Boolean(state.token_present ?? state.tokenPresent),
    lastAdmission: state.last_admission || state.lastAdmission || '',
  };
}
