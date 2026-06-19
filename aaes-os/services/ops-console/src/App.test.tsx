import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { OpsConsoleView } from './App.js';

describe('OpsConsoleView', () => {
  it('renders the MRI, enforcement, and meta constitutional cockpits with seeded data', () => {
    const html = renderToString(
      <OpsConsoleView
        telemetry={{
          drift: { score: 0.2, totalFaults: 2, uniquePatterns: 1, topPatterns: [] },
          topPatterns: [],
          lastFaults: [],
          patchTimeline: [],
        }}
        mriV2={{
          state_vector: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
          delta_state: { continuity: 0.08, governance: -0.04, memory: 0.11, coordination: -0.02, confidence: 0.06 },
          trajectory_vector: { continuity: 0.06, governance: -0.03, memory: 0.08, coordination: -0.01, magnitude: 0.1, confidenceWeightedMagnitude: 0.08, confidence_weighted_magnitude: 0.08 },
          benchmarks: {
            industryAverage: { continuity: 61, governance: 59, memory: 64, coordination: 57, confidence: 70 },
            topQuartile: { continuity: 78, governance: 74, memory: 82, coordination: 71, confidence: 85 },
            previousMeasurement: { continuity: 64, governance: 72, memory: 64, coordination: 65, confidence: 74 },
            summary: '+11 above industry',
            deltas: [],
            bar_markers: {
              continuity: { current: 72, previous: 64, industry: 61, topQuartile: 78 },
              governance: { current: 68, previous: 72, industry: 59, topQuartile: 74 },
              memory: { current: 75, previous: 64, industry: 64, topQuartile: 82 },
              coordination: { current: 63, previous: 65, industry: 57, topQuartile: 71 },
              confidence: { current: 81, previous: 74, industry: 70, topQuartile: 85 },
            },
          },
          trajectory_signatures: ['stable_continuity_declining_governance'],
          trajectory_breakdown: [],
          projection: [],
          risks: [],
          interventions: [],
          evidence: { beforeConfidence: 74, afterConfidence: 81, meanConfidence: 0.8, confidenceTensor: { observationCompleteness: 0.8, dataQuality: 0.8, sourceReliability: 0.8, temporalFreshness: 0.8, crossEvidenceConsistency: 0.8 } },
          before_after: {
            before: { continuity: 64, governance: 72, memory: 64, coordination: 65, confidence: 74 },
            after: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
          },
        }}
        enforcement={{ events: [{ receiptId: 'cen:1', verdict: 'DENY', reasonCode: 'INVARIANT_VIOLATION' }], status: 'ACTIVE' }}
        meta={{ podId: 'meta_constitutional_collapse', generativeCoreId: 'CML-15', metaInvariantCount: 4 }}
      />,
    );

    expect(html).toContain('MRI Cockpit');
    expect(html).toContain('Enforcement Dashboard');
    expect(html).toContain('Meta-Constitutional Console');
    expect(html).toContain('CML-15');
  });
});
