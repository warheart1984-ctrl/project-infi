export interface AlaPlan {
  normalized: any[]
}

export interface AlaPlanner {
  id: string
  description: string
  plan(proposal: any): AlaPlan
}
