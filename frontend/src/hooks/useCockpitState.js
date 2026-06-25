import { useCallback, useReducer } from 'react';

const initialState = {
  phase: 'idle',
  stewardMode: false,
};

function reducer(state, action) {
  switch (action.type) {
    case 'EVALUATE_LAW':
      return { ...state, phase: 'evaluatingLaw' };
    case 'LAW_EVAL_DONE':
      return { ...state, phase: 'idle' };
    case 'RUN_EPOCH':
      return { ...state, phase: 'runningEpoch' };
    case 'EPOCH_SIM_DONE':
      return { ...state, phase: 'idle' };
    case 'LOAD_EVIDENCE':
      return { ...state, phase: 'loadingEvidence' };
    case 'EVIDENCE_READY':
      return { ...state, phase: 'idle' };
    case 'TOGGLE_STEWARD':
      return { ...state, stewardMode: !state.stewardMode };
    default:
      return state;
  }
}

export function useCockpitState() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const busy = state.phase !== 'idle';

  const startEvaluateLaw = useCallback(() => dispatch({ type: 'EVALUATE_LAW' }), []);
  const finishEvaluateLaw = useCallback(() => dispatch({ type: 'LAW_EVAL_DONE' }), []);
  const startRunEpoch = useCallback(() => dispatch({ type: 'RUN_EPOCH' }), []);
  const finishRunEpoch = useCallback(() => dispatch({ type: 'EPOCH_SIM_DONE' }), []);
  const startLoadEvidence = useCallback(() => dispatch({ type: 'LOAD_EVIDENCE' }), []);
  const finishLoadEvidence = useCallback(() => dispatch({ type: 'EVIDENCE_READY' }), []);
  const toggleStewardMode = useCallback(() => dispatch({ type: 'TOGGLE_STEWARD' }), []);

  return {
    ...state,
    busy,
    startEvaluateLaw,
    finishEvaluateLaw,
    startRunEpoch,
    finishRunEpoch,
    startLoadEvidence,
    finishLoadEvidence,
    toggleStewardMode,
  };
}
