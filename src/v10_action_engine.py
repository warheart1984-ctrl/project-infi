def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
class V10ActionEngine:
    def run(self, context):
        mission = context.get("mission")

        if not mission:
            return _wrap_ul_payload({"status": "idle"})

        step = mission.get("next_step")

        if not step:
            return _wrap_ul_payload({"status": "finished"})

        return _wrap_ul_payload({
            "status": "executed",
            "message": f"Executed step: {step}"
        })