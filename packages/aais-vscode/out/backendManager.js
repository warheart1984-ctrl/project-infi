"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AAISBackendManager = void 0;
const coding_assistant_1 = require("@aaes-os/coding-assistant");
class AAISBackendManager {
    stack = null;
    config;
    constructor(config) {
        this.config = config;
    }
    async initialize() {
        const options = {
            ollamaUrl: this.config.ollamaUrl,
            openRouterApiKey: this.config.getOpenRouterApiKey(),
            groqApiKey: this.config.getGroqApiKey(),
            includeCloudFree: true,
            warmModels: true,
        };
        this.stack = await (0, coding_assistant_1.createFreeCodingStack)(options);
    }
    updateConfig(config) {
        this.config = config;
        // Re-initialize on next request if needed
        this.stack = null;
    }
    async getStack() {
        if (!this.stack) {
            await this.initialize();
        }
        return this.stack;
    }
    getAvailableBackends() {
        return this.stack?.discovery.available.map(a => a.name) ?? [];
    }
    getSkippedBackends() {
        return this.stack?.discovery.skipped ?? [];
    }
    dispose() {
        this.stack = null;
    }
}
exports.AAISBackendManager = AAISBackendManager;
//# sourceMappingURL=backendManager.js.map