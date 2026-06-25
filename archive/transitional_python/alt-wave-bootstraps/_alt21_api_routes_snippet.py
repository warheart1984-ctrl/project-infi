

@app.route("/api/jarvis/creative-core-runtime/status", methods=["GET"])
def get_creative_core_runtime_organ_status():
    try:
        from src.creative_core_runtime_organ import build_creative_core_runtime_status

        return jsonify(
            attach_ul_substrate({'creative_core_runtime': build_creative_core_runtime_status()})
        )
    except Exception as e:
        logger.error(f"Error reading creative_core_runtime_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-core/status", methods=["GET"])
def get_v9_core_organ_status():
    try:
        from src.v9_core_organ import build_v9_core_status

        return jsonify(
            attach_ul_substrate({'v9_core': build_v9_core_status()})
        )
    except Exception as e:
        logger.error(f"Error reading v9_core_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-runtime/status", methods=["GET"])
def get_v9_runtime_organ_status():
    try:
        from src.v9_runtime_organ import build_v9_runtime_status

        return jsonify(
            attach_ul_substrate({'v9_runtime': build_v9_runtime_status()})
        )
    except Exception as e:
        logger.error(f"Error reading v9_runtime_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-core/status", methods=["GET"])
def get_v10_core_organ_status():
    try:
        from src.v10_core_organ import build_v10_core_status

        return jsonify(
            attach_ul_substrate({'v10_core': build_v10_core_status()})
        )
    except Exception as e:
        logger.error(f"Error reading v10_core_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-runtime/status", methods=["GET"])
def get_v10_runtime_organ_status():
    try:
        from src.v10_runtime_organ import build_v10_runtime_status

        return jsonify(
            attach_ul_substrate({'v10_runtime': build_v10_runtime_status()})
        )
    except Exception as e:
        logger.error(f"Error reading v10_runtime_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-action-engine/status", methods=["GET"])
def get_v10_action_engine_organ_status():
    try:
        from src.v10_action_engine_organ import build_v10_action_engine_status

        return jsonify(
            attach_ul_substrate({'v10_action_engine': build_v10_action_engine_status()})
        )
    except Exception as e:
        logger.error(f"Error reading v10_action_engine_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-capability-bridge/status", methods=["GET"])
def get_creative_capability_bridge_organ_status():
    try:
        from src.creative_capability_bridge_organ import build_creative_capability_bridge_status

        return jsonify(
            attach_ul_substrate({'creative_capability_bridge': build_creative_capability_bridge_status()})
        )
    except Exception as e:
        logger.error(f"Error reading creative_capability_bridge_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-operator-handoff/status", methods=["GET"])
def get_creative_operator_handoff_organ_status():
    try:
        from src.creative_operator_handoff_organ import build_creative_operator_handoff_status

        return jsonify(
            attach_ul_substrate({'creative_operator_handoff': build_creative_operator_handoff_status()})
        )
    except Exception as e:
        logger.error(f"Error reading creative_operator_handoff_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-console-interface/status", methods=["GET"])
def get_creative_console_interface_organ_status():
    try:
        from src.creative_console_interface_organ import build_creative_console_interface_status

        return jsonify(
            attach_ul_substrate({'creative_console_interface': build_creative_console_interface_status()})
        )
    except Exception as e:
        logger.error(f"Error reading creative_console_interface_organ status: {e}")
        return jsonify({"error": str(e)}), 500
