import { type AlaPlanner, type AlaPlan } from '../AlaPlanner.types.js'

export class AlaSemanticPlanner implements AlaPlanner {
  id = 'ala-semantic'
  description = 'Semantic rewrite planner'

  plan(proposal: any): AlaPlan {
    const normalized = proposal.operations.map((op: any) => {
      // placeholder for semantic normalization
      return { ...op }
    })

    return { normalized }
  }
}
