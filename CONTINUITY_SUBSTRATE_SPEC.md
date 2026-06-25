# Continuity Substrate Specification (v0.0-v0.2)

## v0.0 - Continuity Exists

Goal: Prove continuity can be visualized.

Features:

- Create Event
- Timeline View
- Lineage View

Data Model:

```ts
Event {
  id: string
  timestamp: number
  name: string
  parentId: string | null
}
```

Acceptance:

- User can create events
- Events appear in timeline
- Clicking an event shows its lineage chain

## v0.1 - Receipts

Goal: Prove continuity can be validated.

Features:

- Issue receipt for any event
- View receipts

Data Model:

```ts
Receipt {
  id: string
  eventId: string
  status: "PASS" | "FAIL"
  details: string
}
```

Acceptance:

- User can issue a receipt for any event
- Receipts appear in receipt list
- Receipts link back to events

## v0.2 - File Continuity

Goal: Prove continuity can represent real artifacts.

Features:

- File Tree
- Editor
- File.Opened event
- File.Saved event
- File history becomes lineage

Acceptance:

- User can open a file
- User can edit and save a file
- File events appear in timeline
- File history forms a lineage chain
