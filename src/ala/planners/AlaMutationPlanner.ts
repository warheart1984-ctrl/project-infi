import { type AlaPlanner, type AlaPlan } from '../AlaPlanner.types.js'

export class AlaMutationPlanner implements AlaPlanner {
  id = 'ala-mutation'
  description = 'Mutation-aware planner'

  plan(proposal: any): AlaPlan {
    const normalized = proposal.operations.map((op: any) => {
      // placeholder for mutation logic
      return { ...op }
    })

    return { normalized }
  }
}
