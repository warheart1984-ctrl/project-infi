import { AlaPlannerRegistry } from './AlaPlannerRegistry.js'

export class AlaRuntime {
  private registry = new AlaPlannerRegistry()

  plan(proposal: any) {
    const planner = this.registry.getPlanner(proposal.goal)
    return planner.plan(proposal)
  }

  apply(plan: any) {
    return { applied: plan.normalized }
  }
}
