from __future__ import annotations

def fast_route(message: str) -> tuple[str | None, str | None]:
    text = message.strip()
    lowered = text.lower()

    if lowered.startswith("calc "):
        return "calculator", text[5:]
    if lowered == "time" or lowered.startswith("time "):
        return "time", ""
    if lowered.startswith("python "):
        return "python", text[7:]
    if lowered.startswith("read "):
        return "read_file", text[5:]
    if lowered == "list files":
        return "list_files", ""
    if lowered.startswith("list files "):
        return "list_files", text[len("list files "):]
    if lowered.startswith("search "):
        return "web_search", text[7:]

    return None, None

def is_cacheable(message: str) -> bool:
    lowered = message.strip().lower()
    prefixes = ["calc ", "time", "python ", "read ", "list files", "search "]
    return any(lowered.startswith(p) for p in prefixes) or len(lowered) < 120
