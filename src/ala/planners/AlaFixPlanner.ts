import { type AlaPlanner, type AlaPlan } from '../AlaPlanner.types.js'

export class AlaFixPlanner implements AlaPlanner {
  id = 'ala-fix'
  description = 'Targeted bug-fix planner'

  plan(proposal: any): AlaPlan {
    const normalized = proposal.operations.map((op: any) => {
      // placeholder for fix logic
      return { ...op }
    })

    return { normalized }
  }
}
