#!/usr/bin/env node
import {
  InMemoryThresholdRegistry,
  pullThresholdHistory,
  generateLineageReport,
  generateThresholdChartSpec,
  defaultInvariantSet,
} from "../index";

const [cmd, ...args] = process.argv.slice(2);

async function main() {
  const registry = new InMemoryThresholdRegistry();

  switch (cmd) {
    case "lineage": {
      const id = args[0];
      if (!id) {
        console.error("Usage: thresholdctl lineage <thresholdId>");
        process.exit(1);
      }
      const history = await pullThresholdHistory(registry, id);
      console.log(generateLineageReport(history));
      break;
    }
    case "chart": {
      const id = args[0];
      if (!id) {
        console.error("Usage: thresholdctl chart <thresholdId>");
        process.exit(1);
      }
      const history = await pullThresholdHistory(registry, id);
      console.log(JSON.stringify(generateThresholdChartSpec(history), null, 2));
      break;
    }
    case "invariants": {
      console.log(JSON.stringify(defaultInvariantSet, null, 2));
      break;
    }
    default:
      console.log(`thresholdctl — continuity-engine CLI

  lineage <id>   Markdown lineage report
  chart <id>     JSON chart spec
  invariants     List default CRK-1 invariants
`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
