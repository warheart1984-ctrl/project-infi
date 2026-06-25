

@app.route("/api/jarvis/naming-protocol/status", methods=["GET"])
def get_naming_protocol_organ_status():
    try:
        from src.naming_protocol_organ import build_naming_protocol_status

        return jsonify(
            attach_ul_substrate({'naming_protocol': build_naming_protocol_status()})
        )
    except Exception as e:
        logger.error(f"Error reading naming_protocol_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/naming-genome/status", methods=["GET"])
def get_naming_genome_organ_status():
    try:
        from src.naming_genome_organ import build_naming_genome_status

        return jsonify(
            attach_ul_substrate({'naming_genome': build_naming_genome_status()})
        )
    except Exception as e:
        logger.error(f"Error reading naming_genome_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-mutation/status", methods=["GET"])
def get_linguistic_mutation_organ_status():
    try:
        from src.linguistic_mutation_organ import build_linguistic_mutation_status

        return jsonify(
            attach_ul_substrate({'linguistic_mutation': build_linguistic_mutation_status()})
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_mutation_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/mythic-engineering-translator/status", methods=["GET"])
def get_mythic_engineering_translator_organ_status():
    try:
        from src.mythic_engineering_translator_organ import build_mythic_engineering_translator_status

        return jsonify(
            attach_ul_substrate({'mythic_engineering_translator': build_mythic_engineering_translator_status()})
        )
    except Exception as e:
        logger.error(f"Error reading mythic_engineering_translator_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-drift-predictor/status", methods=["GET"])
def get_linguistic_drift_predictor_organ_status():
    try:
        from src.linguistic_drift_predictor_organ import build_linguistic_drift_predictor_status

        return jsonify(
            attach_ul_substrate({'linguistic_drift_predictor': build_linguistic_drift_predictor_status()})
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_drift_predictor_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-lineage-viz/status", methods=["GET"])
def get_linguistic_lineage_viz_organ_status():
    try:
        from src.linguistic_lineage_viz_organ import build_linguistic_lineage_viz_status

        return jsonify(
            attach_ul_substrate({'linguistic_lineage_viz': build_linguistic_lineage_viz_status()})
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_lineage_viz_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-remediation/status", methods=["GET"])
def get_linguistic_remediation_organ_status():
    try:
        from src.linguistic_remediation_organ import build_linguistic_remediation_status

        return jsonify(
            attach_ul_substrate({'linguistic_remediation': build_linguistic_remediation_status()})
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_remediation_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-cascade/status", methods=["GET"])
def get_linguistic_cascade_organ_status():
    try:
        from src.linguistic_cascade_organ import build_linguistic_cascade_status

        return jsonify(
            attach_ul_substrate({'linguistic_cascade': build_linguistic_cascade_status()})
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_cascade_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/meta-linguistic-governance/status", methods=["GET"])
def get_meta_linguistic_governance_organ_status():
    try:
        from src.meta_linguistic_governance_organ import build_meta_linguistic_governance_status

        return jsonify(
            attach_ul_substrate({'meta_linguistic_governance': build_meta_linguistic_governance_status()})
        )
    except Exception as e:
        logger.error(f"Error reading meta_linguistic_governance_organ status: {e}")
        return jsonify({"error": str(e)}), 500
