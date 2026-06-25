import React from 'react';

function formatPayload(payload) {
  if (!payload || !Object.keys(payload).length) {
    return '{}';
  }
  return JSON.stringify(payload, null, 2);
}

export default function LineagePanel({ selectedEvent, lineage }) {
  return (
    <section className="nova-coding-agent__panel" aria-label="Selected lineage">
      <div className="nova-coding-agent__panel-header">
        <h2>Lineage</h2>
        <span>{selectedEvent ? selectedEvent.name : 'No event selected'}</span>
      </div>
      <ol className="nova-coding-agent__lineage">
        {lineage.length ? lineage.map((item) => {
          const event = item.event || item;
          const depth = item.depth ?? 0;
          return (
            <li key={`${event.id}-${depth}`}>
              <span className="nova-coding-agent__depth">{depth}</span>
              <div>
                <strong>{event.name}</strong>
                <pre>{formatPayload(event.payload)}</pre>
              </div>
            </li>
          );
        }) : (
          <li className="nova-coding-agent__empty">Select an event to inspect ancestry.</li>
        )}
      </ol>
    </section>
  );
}
