from fastapi import Header, HTTPException, Request, WebSocket
from app.config import APP_BEARER_TOKEN

def require_token(authorization: str | None = Header(default=None)):
    if not APP_BEARER_TOKEN:
        return
    expected = f"Bearer {APP_BEARER_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

def check_sse_token(request: Request) -> None:
    if not APP_BEARER_TOKEN:
        return
    token = request.query_params.get("token", "")
    if token != APP_BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

async def check_ws_token(websocket: WebSocket) -> None:
    if not APP_BEARER_TOKEN:
        return
    token = websocket.query_params.get("token", "")
    if token != APP_BEARER_TOKEN:
        await websocket.close(code=4401)
        raise RuntimeError("Unauthorized websocket")
