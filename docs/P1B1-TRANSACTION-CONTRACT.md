# P1-B1 candidate: atomic pending parsing and durable submission receipt

Parent fe8eaa662ef89d468ccd93850487f04880e313c5 passed P1-A synthetic Mac acceptance: 29 PASS, 2 deferred gaps, no errors/regressions.
This candidate addresses 12 and 13, not yet runtime-qualified.

- SQLite is the authoritative commit boundary. Raw input and backup outbox are committed together; an optional caller-generated request_key provides exact-retry deduplication and rejects key reuse with different normalized input. Legacy callers without a key still create distinct records. Do not deduplicate different events just because text matches.
- Parser commits candidates and source transition atomically under BEGIN IMMEDIATE. Legacy partially parsed pending inputs are held for explicit reconciliation. No automatic deletion.
- JSONL is a recoverable projection, not a second transactional database. Commit receipt distinguishes COMMITTED / backup SYNCED or PENDING. Explicit retry uses the durable outbox. Stable event id and atomic file replacement avoid double append after successful file write but failed acknowledgment. Existing JSONL rows remain unchanged; malformed rows fail closed.
- One SQLite database owns one JSONL destination, not multiple independent writers. Rewriting a full file is a bounded initial desktop design, NOT a large-scale production backup strategy. A filesystem/power loss can still lose the projection; independent backup and restore verification remain required. No automatic startup retries or historical migration.
- Existing direct low-level methods remain for legacy compatibility. This is not yet an authenticated API. HTTP caller must derive scoped identity and key from authentication. OCR import claim/transaction, confirmed-record revision/audit atomicity, individual person-hours, NotiBase linkage, and actual platform integration are subsequent gates.
- All validation is synthetic. No live database, deployment, or main changes.
