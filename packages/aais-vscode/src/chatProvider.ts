import * as vscode from 'vscode';
import { AAISBackendManager } from './backendManager';
import { AAISConfig } from './config';

export class AAISChatProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'aaisChatView';
  private _view?: vscode.WebviewView;
  private _messages: ChatMessage[] = [];
  private _streaming = false;

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly backendManager: AAISBackendManager,
    private readonly config: AAISConfig
  ) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ): void {
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

  public focus(): void {
    this._view?.show?.(true);
  }

  public refresh(): void {
    this._view?.webview.postMessage({ type: 'refresh', config: this._getConfigSnapshot() });
  }

  private async _handleSend(text: string): Promise<void> {
    if (this._streaming || !text.trim()) return;
    
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
    } catch (error) {
      this._messages[assistantMsgIndex] = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: Date.now(),
        streaming: false,
        error: true,
      };
    } finally {
      this._streaming = false;
      this._postMessages();
    }
  }

  private _postMessages(): void {
    this._view?.webview.postMessage({
      type: 'messages',
      messages: this._messages,
      config: this._getConfigSnapshot(),
    });
  }

  private _getConfigSnapshot() {
    return {
      governanceMode: this.config.governanceMode,
      preferredBackend: this.config.preferredBackend,
      availableBackends: this.backendManager.getAvailableBackends(),
      skippedBackends: this.backendManager.getSkippedBackends(),
    };
  }

  private _getHtml(): string {
    const scriptUri = this._view?.webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, 'media', 'chat.js')
    ) ?? '';
    const styleUri = this._view?.webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, 'media', 'chat.css')
    ) ?? '';

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

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  streaming?: boolean;
  backend?: string;
  error?: boolean;
}