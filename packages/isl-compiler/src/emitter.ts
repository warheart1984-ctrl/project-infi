import type{SubstratePlan}from './models.js'; export class PlanEmitter{emit(plan:SubstratePlan):SubstratePlan{return structuredClone(plan);}}
