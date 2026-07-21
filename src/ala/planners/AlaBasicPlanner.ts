import { type AlaPlanner, type AlaPlan } from '../AlaPlanner.types.js'

export class AlaBasicPlanner implements AlaPlanner {
  id = 'ala-basic'
  description = 'Deterministic normalization of operations'

  plan(proposal: any): AlaPlan {
    const normalized = [...proposal.operations]
      .sort((a, b) => (a.file + a.type).localeCompare(b.file + b.type))

    return { normalized }
  }
}
