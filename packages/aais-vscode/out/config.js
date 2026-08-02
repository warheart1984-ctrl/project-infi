"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.AAISConfig = void 0;
const vscode = __importStar(require("vscode"));
class AAISConfig {
    config;
    constructor() {
        this.config = vscode.workspace.getConfiguration('aais');
    }
    reload() {
        this.config = vscode.workspace.getConfiguration('aais');
    }
    get governanceMode() {
        return this.config.get('governanceMode', true);
    }
    async setGovernanceMode(value) {
        await this.config.update('governanceMode', value, vscode.ConfigurationTarget.Global);
        this.reload();
    }
    get preferredBackend() {
        return this.config.get('preferredBackend', 'auto');
    }
    async setPreferredBackend(value) {
        await this.config.update('preferredBackend', value, vscode.ConfigurationTarget.Global);
        this.reload();
    }
    get ollamaUrl() {
        return this.config.get('ollamaUrl', 'http://127.0.0.1:11434');
    }
    get autoDetect() {
        return this.config.get('autoDetect', true);
    }
    getGroqApiKey() {
        return process.env.GROQ_API_KEY;
    }
    getOpenRouterApiKey() {
        return process.env.OPENROUTER_API_KEY;
    }
    getCursorApiKey() {
        return process.env.CURSOR_API_KEY;
    }
}
exports.AAISConfig = AAISConfig;
//# sourceMappingURL=config.js.map