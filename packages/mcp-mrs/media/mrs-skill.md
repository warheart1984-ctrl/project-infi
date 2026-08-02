# MRS Workflow Skill

Use `render_rt4d_preview` whenever the user requests an RT4D, 4D, governed, replayable, or constitutionally evidenced render.

## Rules

1. Use `render_rt4d_preview` whenever the user requests an RT4D, 4D, governed, replayable, or constitutionally evidenced render.
2. Never claim that a scene was rendered unless the MCP tool returned a successful evidence envelope.
3. Never convert assistant-generated imagery into `substrate_verified` evidence.
4. Report `evidenceStatus` and `promotionStatus` exactly as returned.
5. If the tool returns an error, do not retry with a different backend or simulate a result.
6. If `evidenceStatus` is not `substrate_verified`, do not present the result as a constitutional render.
7. If `promotionStatus` is `not_promoted_to_ciems`, state that the render is not yet eligible for CIEMS promotion.

## Failure Behavior

- `MRS_ENGINE_UNAVAILABLE`: The MRS engine is not reachable. Do not fall back to AAIS or any other renderer. Report the error honestly.
- `ENGINE_EVIDENCE_INCOMPLETE`: The engine returned an invalid or incomplete evidence bundle. Do not fabricate missing fields.
- `ENGINE_EVIDENCE_INTEGRITY_ERROR`: Hash mismatch between scene creation and render steps. Report the integrity failure.
- `INVALID_INPUT`: The user's request does not conform to the tool schema. Ask for the missing or invalid fields.

## Output Format

The tool returns:
- A PNG image (base64) of the rendered scene
- A structured evidence bundle with hashes, IDs, and status fields

Present both to the user. The image is the visual result; the evidence bundle is the constitutional proof.