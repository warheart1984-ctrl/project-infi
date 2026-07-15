import { type AlaPlanner, type AlaPlan } from '../AlaPlanner.types.js'

export class AlaRefactorPlanner implements AlaPlanner {
  id = 'ala-refactor'
  description = 'Structural refactor planner'

  plan(proposal: any): AlaPlan {
    const normalized = proposal.operations.map((op: any) => {
      // placeholder for refactor logic
      return { ...op }
    })

    return { normalized }
  }
}
