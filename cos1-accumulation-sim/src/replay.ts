import * as fs from "fs";
import * as readline from "readline";
import { EventBus } from "./eventBus.js";
import { JPSSContributionEvent } from "./domain.js";
import { initialState, applyEvent } from "./state.js";

export async function replay(filePath: string, timeTravel: boolean) {
  const bus = new EventBus<JPSSContributionEvent>();
  let state = initialState();

  bus.subscribe((ev) => {
    state = applyEvent(state, ev);
    if (timeTravel) {
      console.log("STATE AFTER", ev.id, {
        origin: state.eventOrigins[ev.id] ?? null,
        mode: state.events.at(-1)?.mode ?? null,
        A_t: state.continuity.accumulation.value,
        plt1: state.continuity.plt1,
        mat3_la: state.continuity.mat3,
        interpretation: state.continuity.interpretation,
      });
    }
  });

  const rl = readline.createInterface({
    input: fs.createReadStream(filePath),
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    if (!line.trim()) continue;
    const ev = JSON.parse(line) as JPSSContributionEvent;
    bus.publish(ev);
  }

  console.log("FINAL STATE", {
    eventOrigins: state.eventOrigins,
    interpretation: state.continuity.interpretation,
    A_t: state.continuity.accumulation,
    plt1: state.continuity.plt1,
    mat3_la: state.continuity.mat3,
    pla: state.continuity.pla,
    la: state.continuity.la,
    sa: state.continuity.sa,
    coupling: state.continuity.coupling,
    gravity: state.continuity.gravity,
    invariants: state.continuity.invariants,
    stewardCandidates: state.stewardCandidates,
  });

  return state;
}

const file = process.argv[2];
const mode = process.argv[3] || "final";

if (!file) {
  console.error("Usage: node dist/replay.js events.jsonl [time|final]");
  process.exit(1);
}

replay(file, mode === "time");
