import type { AgentAction } from "../types/actions";
import { recordReceipt } from "../governance/receipts";
import { updateContinuity } from "../continuity/substrate";
import { emitAction, emitReceipt } from "../events/lifecycle";
import { applyDiff } from "../runtime/workspace";

export async function execute(action: AgentAction): Promise<unknown> {
  emitAction(action);

  switch (action.type) {
    case "edit":
    case "create": {
      const diff = typeof action.payload.diff === "string" ? action.payload.diff : "";
      if (diff) await applyDiff(diff);
      break;
    }
    case "run":
      break;
    default:
      break;
  }

  const receipt = await recordReceipt(action, ["executed"]);
  await updateContinuity(action);
  emitReceipt(receipt);
  return { ok: true, receipt };
}
