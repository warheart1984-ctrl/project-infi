import * as vscode from 'vscode';
import { AAISBackendManager } from './backendManager';
import { AAISConfig } from './config';
export declare class AAISChatProvider implements vscode.WebviewViewProvider {
    private readonly _extensionUri;
    private readonly backendManager;
    private readonly config;
    static readonly viewType = "aaisChatView";
    private _view?;
    private _messages;
    private _streaming;
    constructor(_extensionUri: vscode.Uri, backendManager: AAISBackendManager, config: AAISConfig);
    resolveWebviewView(webviewView: vscode.WebviewView, _context: vscode.WebviewViewResolveContext, _token: vscode.CancellationToken): void;
    focus(): void;
    refresh(): void;
    private _handleSend;
    private _postMessages;
    private _getConfigSnapshot;
    private _getHtml;
}
//# sourceMappingURL=chatProvider.d.ts.map