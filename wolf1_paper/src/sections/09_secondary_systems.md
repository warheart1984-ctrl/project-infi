# 9. Secondary Systems and Active‑Over‑Relay

WOLF‑1 defines primary and secondary systems for all critical functions.

## 9.1 Secondary System Architecture

| Function | Primary | Secondary |
|----------|----------|-----------|
| Power | Full controller | Minimal supervisor |
| Attitude/Propulsion | Full flight computer | Safe‑pointing controller |
| Comms | Full RF/optical | Minimal beacon mode |

Secondary systems activate during safe‑mode or primary failure.

---

## 9.2 Active‑Over‑Relay Protocol

- Ground sends signed recovery commands
- CAS validates signatures
- Secondary systems maintain governance floor
- Primary systems restored gradually

---
