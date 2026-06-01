# P15 Universal Substrate Proof (Windows / macOS / Android)

Status: **asserted** (contract tier; boot proof pending per platform).

Authority: `docs/forge-universal-substrate-program.md`.

## Claim

Forge registers and wires universal OS replay adapters and inject backends without breaking P10/P11 separation.

## Verification

```bash
python3 wolf-cog-os/scripts/validate-substrate-invariants.py --mode fail
python3 wolf-cog-os/scripts/validate-replay-adapter.py --mode fail
python3 wolf-cog-os/scripts/validate-rootfs-backend.py --backend winpe-backend --registry-only --mode fail
python3 -m unittest tests.test_universal_substrate
make forge-platform-gate
```

## Platform boot proof debt

| Platform | Required host proof |
|---|---|
| Windows | wimapply extract + BCD-preserving replay ISO |
| macOS | hdiutil/APFS mount + sealed snapshot check |
| Android | lpunpack + QEMU boot from repacked super |
