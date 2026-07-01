# Governed Document Pipeline for AAES-OS / WOLF-1

DOC_ID      ?= wolf1-arch
VERSION_FILE = .governance/version.yaml
BUILD_DIR   = build
CTS_DIR     = cts
META_DIR    = metadata
REC_DIR     = governance/receipts

.PHONY: all cts pdf changelog amendments receipt receipt-index dashboard enforce traceability zenodo github docs adr-index diagrams sync clean install

all: enforce cts pdf changelog amendments receipt receipt-index adr-index diagrams

install:
	npm install

sync:
	node src/sync_sections_from_master.js

cts:
	@echo "[CTS] Running governance validation..."
	@bash $(CTS_DIR)/run_all.sh 2>/dev/null || node $(CTS_DIR)/run_all.mjs

enforce:
	@echo "[GOV] Governance enforcement (traceability + CTS)..."
	@bash scripts/enforce_governance.sh 2>/dev/null || (node -e "require('child_process').spawnSync('python',['scripts/validate_traceability_chain.py'],{stdio:'inherit',cwd:process.cwd(),shell:true})" && node cts/run_all.mjs)

traceability:
	@node scripts/validate_traceability_chain.mjs

pdf: cts
	@echo "[PDF] Building governed PDFs..."
	@DOC_ID=$(DOC_ID) node build.mjs $(DOC_ID) --skip-cts

changelog:
	@echo "[CHANGELOG] Updating changelog from ADRs..."
	@node scripts/update_changelog.mjs $(DOC_ID)

amendments:
	@echo "[AMENDMENTS] Generating amendment diffs..."
	@node scripts/gen_amendment_diffs.mjs

receipt:
	@echo "[RECEIPT] Emitting governance receipt..."
	@bash scripts/gen_build_receipt.sh $(DOC_ID) $(BUILD_DIR) 2>/dev/null || node scripts/gen_build_receipt.mjs $(DOC_ID) $(BUILD_DIR)

receipt-index:
	@echo "[RECEIPT-INDEX] Building dashboard artifacts..."
	@node scripts/gen_dashboard_artifacts.mjs

dashboard: receipt-index
	@echo "[DASHBOARD] Ready at governance/dashboard.html"

pdf: cts
	@echo "[PDF] Building governed PDFs..."
	@DOC_ID=$(DOC_ID) node build.mjs $(DOC_ID) --skip-cts

changelog:
	@echo "[CHANGELOG] Updating changelog from ADRs..."
	@node scripts/update_changelog.mjs $(DOC_ID)

amendments:
	@echo "[AMENDMENTS] Generating amendment diffs..."
	@node scripts/gen_amendment_diffs.mjs

receipt:
	@echo "[RECEIPT] Emitting governance receipt..."
	@node scripts/gen_build_receipt.mjs $(DOC_ID) $(BUILD_DIR)

zenodo:
	@echo "[ZENODO] Publishing to Zenodo (if tagged)..."
	@bash scripts/publish_zenodo.sh $(DOC_ID) $(BUILD_DIR) $(META_DIR)

github:
	@echo "[GITHUB] Publishing to GitHub Releases (if tagged)..."
	@bash scripts/publish_github_release.sh $(DOC_ID) $(BUILD_DIR)

docs:
	@echo "[DOCS] Publishing to documentation portal..."
	@bash scripts/publish_docs.sh $(DOC_ID) $(BUILD_DIR)

adr-index:
	@echo "[ADR] Regenerating ADR index..."
	@node scripts/gen_adr_index.mjs

diagrams:
	@echo "[DIAGRAMS] Generating diagrams from specs..."
	@node scripts/gen_diagrams_from_specs.mjs

clean:
	rm -rf $(BUILD_DIR)
	rm -f governance/receipts/*.json
	@echo '[]' > governance/receipts-index.json
