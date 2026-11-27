# P1-A — deterministic contract repairs (candidate)

Parent: 2fbaf0ee6a5742d7840ec8a6136dafd768aafc96

Synthetic baseline P0.3: 12 PASS / 11 CONTRACT_GAP / 0 REGRESSION / 0 ERROR; no GUI or NotiVision integration qualification. This branch addresses gaps 03, 05, 06, 08, 11, 14, 17, 18, 19. It does not claim that the repairs have passed runtime acceptance.

- Parser validates dates/clocks, requires explicit overnight evidence, and handles common negated/uncertain statuses. Rule output is still a candidate, not verified device recovery.
- Employee lookup requires exactly one active matching row. Same-name ambiguity must not be silently resolved.
- New SQLite connections enable foreign keys. No historical rows are deleted or migrated; existing orphan audit remains mandatory before actual use.
- All existing workbook strings are literal; no workbook formula is intended. Preserve five sheets and numeric cells.
- OCR import requires confirmed state; imported state is terminal at service level. Cross-worker atomicity is still open.

P1-B remaining: gap 12 atomic parse + status transition with fault injection and concurrency; gap 13 durable SQLite-authoritative backup outbox with explicit submission receipt and retry; OCR atomic claim/import; review/audit transaction; migration preflight on an authorized copy only. No real input, history, database, platform or deployment changes. No external API enablement.
