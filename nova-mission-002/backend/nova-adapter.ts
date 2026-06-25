import { crk2Service } from "./crk2-service";
import { controlTowerService } from "./control-tower-service";
import { eventsGateway } from "./events-gateway";

export async function evaluateNovaAction(
  action: { type: string; payload?: Record<string, unknown> },
  context: Record<string, unknown>
): Promise<{ allowed: boolean; result: ReturnType<typeof crk2Service.evaluateAction> }> {
  const result = crk2Service.evaluateAction(action, context);
  if (!result.ok) {
    eventsGateway.emit("drift", {
      reason: result.reason,
      detail: result.detail,
    });
    return { allowed: false, result };
  }
  return { allowed: true, result };
}

export const novaAdapter = {
  evaluateNovaAction,
  crk2: crk2Service,
  controlTower: controlTowerService,
  events: eventsGateway,
};
