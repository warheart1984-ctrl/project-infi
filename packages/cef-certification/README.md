# `@aaes-os/cef-certification`

CEF Certification Engine **stub**. Calls `@aaes-os/cef-core` for profile validation and the claim≠evidence promotion gate.

Does **not** invent authority signatures. Certificates stay `DRAFT` / `unpromoted` until evidence is approved, checks are non-pending, and a signature is present.

Spec: `docs/release/cef/CERTIFICATION_ENGINE_V1.md`
