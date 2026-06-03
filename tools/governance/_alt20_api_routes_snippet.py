

@app.route("/api/jarvis/memory-smith/status", methods=["GET"])
def get_memory_smith_organ_status():
    try:
        from src.memory_smith_organ import build_memory_smith_status

        return jsonify(
            attach_ul_substrate({'memory_smith': build_memory_smith_status()})
        )
    except Exception as e:
        logger.error(f"Error reading memory_smith_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-workspace/status", methods=["GET"])
def get_operator_workspace_organ_status():
    try:
        from src.operator_workspace_organ import build_operator_workspace_status

        return jsonify(
            attach_ul_substrate({'operator_workspace': build_operator_workspace_status()})
        )
    except Exception as e:
        logger.error(f"Error reading operator_workspace_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/jarvis-runs/status", methods=["GET"])
def get_jarvis_runs_organ_status():
    try:
        from src.jarvis_runs_organ import build_jarvis_runs_status

        return jsonify(
            attach_ul_substrate({'jarvis_runs': build_jarvis_runs_status()})
        )
    except Exception as e:
        logger.error(f"Error reading jarvis_runs_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/state-hygiene/status", methods=["GET"])
def get_state_hygiene_organ_status():
    try:
        from src.state_hygiene_organ import build_state_hygiene_status

        return jsonify(
            attach_ul_substrate({'state_hygiene': build_state_hygiene_status()})
        )
    except Exception as e:
        logger.error(f"Error reading state_hygiene_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/blueprint-posture/status", methods=["GET"])
def get_blueprint_posture_organ_status():
    try:
        from src.blueprint_posture_organ import build_blueprint_posture_status

        return jsonify(
            attach_ul_substrate({'blueprint_posture': build_blueprint_posture_status()})
        )
    except Exception as e:
        logger.error(f"Error reading blueprint_posture_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workflow-interfaces/status", methods=["GET"])
def get_workflow_interfaces_organ_status():
    try:
        from src.workflow_interfaces_organ import build_workflow_interfaces_status

        return jsonify(
            attach_ul_substrate({'workflow_interfaces': build_workflow_interfaces_status()})
        )
    except Exception as e:
        logger.error(f"Error reading workflow_interfaces_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/platform-console-interfaces/status", methods=["GET"])
def get_platform_console_interfaces_organ_status():
    try:
        from src.platform_console_interfaces_organ import build_platform_console_interfaces_status

        return jsonify(
            attach_ul_substrate({'platform_console_interfaces': build_platform_console_interfaces_status()})
        )
    except Exception as e:
        logger.error(f"Error reading platform_console_interfaces_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-console-interface/status", methods=["GET"])
def get_operator_console_interface_organ_status():
    try:
        from src.operator_console_interface_organ import build_operator_console_interface_status

        return jsonify(
            attach_ul_substrate({'operator_console_interface': build_operator_console_interface_status()})
        )
    except Exception as e:
        logger.error(f"Error reading operator_console_interface_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/nova-workspace-interface/status", methods=["GET"])
def get_nova_workspace_interface_organ_status():
    try:
        from src.nova_workspace_interface_organ import build_nova_workspace_interface_status

        return jsonify(
            attach_ul_substrate({'nova_workspace_interface': build_nova_workspace_interface_status()})
        )
    except Exception as e:
        logger.error(f"Error reading nova_workspace_interface_organ status: {e}")
        return jsonify({"error": str(e)}), 500
