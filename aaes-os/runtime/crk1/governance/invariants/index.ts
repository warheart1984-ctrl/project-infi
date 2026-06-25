export { noEmptyPayload } from './noEmptyPayload.js';
export { mustEmitExecuteSpan } from './mustEmitExecuteSpan.js';

import { mustEmitExecuteSpan } from './mustEmitExecuteSpan.js';
import { noEmptyPayload } from './noEmptyPayload.js';
import type { Invariant } from '../types.js';

export const coreInvariants: Invariant[] = [noEmptyPayload, mustEmitExecuteSpan];
