import { type AlaPlanner } from './AlaPlanner.types.js'
import { AlaBasicPlanner } from './planners/AlaBasicPlanner.js'
import { AlaSemanticPlanner } from './planners/AlaSemanticPlanner.js'
import { AlaMutationPlanner } from './planners/AlaMutationPlanner.js'
import { AlaRefactorPlanner } from './planners/AlaRefactorPlanner.js'
import { AlaFixPlanner } from './planners/AlaFixPlanner.js'

export class AlaPlannerRegistry {
  private planners: Record<string, AlaPlanner> = {
    refactor: new AlaRefactorPlanner(),
    rewrite: new AlaSemanticPlanner(),
    fix: new AlaFixPlanner(),
    mutation: new AlaMutationPlanner(),
    default: new AlaBasicPlanner(),
  }

  getPlanner(goal: string): AlaPlanner {
    return this.planners[goal] || this.planners.default
  }
}
