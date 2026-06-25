export interface RegisteredAgent {
  id: string;
  status: "online" | "offline" | "drift" | "error";
  kernelVersion: string;
}

const agents = new Map<string, RegisteredAgent>();

export const agentRegistry = {
  register(id: string, kernelVersion = "CRK-2"): RegisteredAgent {
    const agent: RegisteredAgent = { id, status: "online", kernelVersion };
    agents.set(id, agent);
    return agent;
  },

  list(): RegisteredAgent[] {
    return [...agents.values()];
  },

  get(id: string): RegisteredAgent | undefined {
    return agents.get(id);
  },

  updateStatus(id: string, status: RegisteredAgent["status"]): void {
    const agent = agents.get(id);
    if (agent) agents.set(id, { ...agent, status });
  },
};
