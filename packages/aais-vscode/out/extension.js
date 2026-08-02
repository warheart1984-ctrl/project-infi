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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const chatProvider_1 = require("./chatProvider");
const backendManager_1 = require("./backendManager");
const config_1 = require("./config");
let chatProvider;
let backendManager;
async function activate(context) {
    const config = new config_1.AAISConfig();
    backendManager = new backendManager_1.AAISBackendManager(config);
    await backendManager.initialize();
    chatProvider = new chatProvider_1.AAISChatProvider(context.extensionUri, backendManager, config);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('aaisChatView', chatProvider), vscode.commands.registerCommand('aais.openChat', () => {
        vscode.commands.executeCommand('workbench.view.extension.aais-chat');
        chatProvider.focus();
    }), vscode.commands.registerCommand('aais.configure', () => {
        vscode.commands.executeCommand('workbench.action.openSettings', 'aais');
    }), vscode.commands.registerCommand('aais.toggleGovernance', async () => {
        const newValue = !config.governanceMode;
        await config.setGovernanceMode(newValue);
        vscode.window.showInformationMessage(`AAIS Governance Mode: ${newValue ? 'ON' : 'OFF'}`);
        chatProvider.refresh();
    }), vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('aais')) {
            config.reload();
            backendManager.updateConfig(config);
            chatProvider.refresh();
        }
    }));
    vscode.window.showInformationMessage('AAIS Coding Assistant activated');
}
function deactivate() {
    backendManager?.dispose();
}
//# sourceMappingURL=extension.js.map