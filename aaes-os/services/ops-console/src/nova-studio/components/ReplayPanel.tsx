import type { ReplayCheckpoint, TimelineEvent } from '../state/substrateStreams.js';

export function ReplayPanel({
  checkpoints,
  timeline,
}: {
  checkpoints: ReplayCheckpoint[];
  timeline: TimelineEvent[];
}) {
  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Replay &amp; Receipts</h3>
      <p>Replay checkpoints {checkpoints.length}</p>
      <ol>
        {timeline.map((event) => (
          <li key={event.id}>{event.timestamp} {event.label}</li>
        ))}
      </ol>
    </div>
  );
}
