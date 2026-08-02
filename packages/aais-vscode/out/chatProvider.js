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
exports.AAISChatProvider = void 0;
const vscode = __importStar(require("vscode"));
class AAISChatProvider {
    _extensionUri;
    backendManager;
    config;
    static viewType = 'aaisChatView';
    _view;
    _messages = [];
    _streaming = false;
    constructor(_extensionUri, backendManager, config) {
        this._extensionUri = _extensionUri;
        this.backendManager = backendManager;
        this.config = config;
    }
    resolveWebviewView(webviewView, _context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };
        webviewView.webview.html = this._getHtml();
        webviewView.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'send':
                    await this._handleSend(message.text);
                    break;
                case 'clear':
                    this._messages = [];
                    this._postMessages();
                    break;
                case 'setBackend':
                    await this.config.setPreferredBackend(message.backend);
                    break;
                case 'toggleGovernance':
                    await this.config.setGovernanceMode(!this.config.governanceMode);
                    break;
            }
        });
    }
    focus() {
        this._view?.show?.(true);
    }
    refresh() {
        this._view?.webview.postMessage({ type: 'refresh', config: this._getConfigSnapshot() });
    }
    async _handleSend(text) {
        if (this._streaming || !text.trim())
            return;
        this._streaming = true;
        this._messages.push({ role: 'user', content: text, timestamp: Date.now() });
        this._postMessages();
        const assistantMsgIndex = this._messages.length;
        this._messages.push({ role: 'assistant', content: '', timestamp: Date.now(), streaming: true });
        this._postMessages();
        try {
            const stack = await this.backendManager.getStack();
            const identity = { actorId: 'vscode-user', role: 'developer' };
            const shell = this.config.governanceMode
                ? stack.assistant.nova(identity, {
                    preferredBackend: this.config.preferredBackend === 'auto' ? undefined : this.config.preferredBackend
                })
                : stack.assistant.nova(identity, {
                    preferredBackend: this.config.preferredBackend === 'auto' ? undefined : this.config.preferredBackend
                });
            const response = await shell.runCommand(text);
            this._messages[assistantMsgIndex] = {
                role: 'assistant',
                content: response.output.text,
                timestamp: Date.now(),
                streaming: false,
                backend: response.backendName,
            };
        }
        catch (error) {
            this._messages[assistantMsgIndex] = {
                role: 'assistant',
                content: `Error: ${error instanceof Error ? error.message : String(error)}`,
                timestamp: Date.now(),
                streaming: false,
                error: true,
            };
        }
        finally {
            this._streaming = false;
            this._postMessages();
        }
    }
    _postMessages() {
        this._view?.webview.postMessage({
            type: 'messages',
            messages: this._messages,
            config: this._getConfigSnapshot(),
        });
    }
    _getConfigSnapshot() {
        return {
            governanceMode: this.config.governanceMode,
            preferredBackend: this.config.preferredBackend,
            availableBackends: this.backendManager.getAvailableBackends(),
            skippedBackends: this.backendManager.getSkippedBackends(),
        };
    }
    _getHtml() {
        const scriptUri = this._view?.webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'chat.js')) ?? '';
        const styleUri = this._view?.webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'chat.css')) ?? '';
        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="${styleUri}" rel="stylesheet">
  <title>AAIS Chat</title>
</head>
<body>
  <div id="app"></div>
  <script src="${scriptUri}"></script>
</body>
</html>`;
    }
}
exports.AAISChatProvider = AAISChatProvider;
//# sourceMappingURL=chatProvider.js.map