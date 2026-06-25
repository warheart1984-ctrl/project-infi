"""Combined local mesh app — identity, asset, evidence, validation on one port."""

from __future__ import annotations

from fastapi import FastAPI

from services.runtime.mesh_handlers import mesh_router

app = FastAPI(title="CORI Runtime Mesh", version="0.1.0")
app.include_router(mesh_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "runtime_mesh"}
