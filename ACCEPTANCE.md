# Acceptance Tests - v0.0 to v0.2

## v0.0 - Continuity Exists

### Test 1: Create Event

Steps:

1. POST /events with name="TestEvent"

Expected:

- Event appears in GET /events

### Test 2: Timeline

Steps:

1. Create multiple events

Expected:

- Events appear in chronological order

### Test 3: Lineage

Steps:

1. Create event with parentId

Expected:

- GET /lineage/{id} returns ancestry chain

## v0.1 - Receipts

### Test 4: Issue Receipt

Steps:

1. POST /events/{id}/receipt

Expected:

- Receipt appears in GET /receipts

### Test 5: Receipt Linking

Steps:

1. Issue receipt for event

Expected:

- Receipt.eventId matches event.id

## v0.2 - File Continuity

### Test 6: Open File

Steps:

1. POST /file/open?path=...

Expected:

- File.Opened event emitted

### Test 7: Save File

Steps:

1. POST /file/save with content

Expected:

- File.Saved event emitted

### Test 8: File History Lineage

Steps:

1. Save file multiple times

Expected:

- Lineage shows chain of File.Saved events
