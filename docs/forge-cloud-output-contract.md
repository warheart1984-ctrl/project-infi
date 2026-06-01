# Forge Cloud Output Contract (P8)

Status: canonical cloud image output contract.

Registry: `wolf-cog-os/forge/outputs/registry.json`

## Supported formats (contract)

| Format | Status | Extension |
|---|---|---|
| `raw-img` | stub | `.img` |
| `qcow2` | stub | `.qcow2` |
| `vhd` | stub | `.vhd` |
| `ami` | stub | `.ami.json` |

## Dispatcher

```bash
bash wolf-cog-os/scripts/lib/emit-cloud-image.sh /path/to/image.iso raw-img /path/to/out.img
```

## Validation

```bash
python3 wolf-cog-os/scripts/validate-cloud-output.py --format raw-img --registry-only --mode fail
```

## Multi-arch

Cloud format availability per arch is declared in `wolf-cog-os/forge/platforms/arch-matrix.json`.
