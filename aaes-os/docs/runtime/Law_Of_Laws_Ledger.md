# Law-of-Laws Ledger

The law-of-laws ledger anchors CML-15 and the meta-constitutional collapse record.

## Entries
The MVP ledger accepts:

- `pod`
- `meta_invariant`
- `constitutional_singularity`
- `collapse_record`

## Hash Chain
Each entry stores:

- sequence;
- entry type;
- subject ID;
- payload;
- issued timestamp;
- previous hash;
- entry hash.

The entry hash is a stable SHA3-256 hash of the entry body. This makes the ledger append-only for operator evidence purposes.
