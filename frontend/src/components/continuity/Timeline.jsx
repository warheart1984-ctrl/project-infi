import React from 'react';
import { FiFileText, FiPlus } from 'react-icons/fi';

function getEventTime(event) {
  return event?.createdAt || event?.created_at || event?.timestamp || '';
}

function formatTime(value) {
  if (!value) {
    return 'pending';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

export default function Timeline({
  events,
  loadingTimeline,
  manualEventName,
  onManualEventNameChange,
  onCreateEvent,
  onSelectEvent,
  selectedEventId,
  busyAction,
}) {
  return (
    <section className="nova-coding-agent__panel">
      <div className="nova-coding-agent__panel-header">
        <h2>Timeline</h2>
        <span>{loadingTimeline ? 'Loading' : `${events.length} events`}</span>
      </div>
      <div className="nova-coding-agent__manual-event">
        <label className="nova-coding-agent__field">
          <span>Event name</span>
          <input value={manualEventName} onChange={(event) => onManualEventNameChange(event.target.value)} />
        </label>
        <button type="button" onClick={onCreateEvent} disabled={busyAction === 'event'}>
          <FiPlus aria-hidden="true" />
          <span>Create event</span>
        </button>
      </div>
      <div className="nova-coding-agent__timeline" aria-label="Continuity timeline">
        {events.length ? events.map((event) => (
          <button
            className={`nova-coding-agent__event ${selectedEventId === event.id ? 'is-selected' : ''}`}
            key={event.id}
            type="button"
            onClick={() => onSelectEvent(event)}
          >
            <FiFileText aria-hidden="true" />
            <span>
              <strong>{event.name}</strong>
              <small>{formatTime(getEventTime(event))}</small>
            </span>
          </button>
        )) : (
          <p className="nova-coding-agent__empty">No continuity events yet.</p>
        )}
      </div>
    </section>
  );
}
