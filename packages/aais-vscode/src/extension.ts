import * as vscode from 'vscode';
import { AAISChatProvider } from './chatProvider';
import { AAISBackendManager } from './backendManager';
import { AAISConfig } from './config';

let chatProvider: AAISChatProvider;
let backendManager: AAISBackendManager;

export async function activate(context: vscode.ExtensionContext) {
  const config = new AAISConfig();
  backendManager = new AAISBackendManager(config);
  await backendManager.initialize();

  chatProvider = new AAISChatProvider(context.extensionUri, backendManager, config);
  
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('aaisChatView', chatProvider),
    
    vscode.commands.registerCommand('aais.openChat', () => {
      vscode.commands.executeCommand('workbench.view.extension.aais-chat');
      chatProvider.focus();
    }),
    
    vscode.commands.registerCommand('aais.configure', () => {
      vscode.commands.executeCommand('workbench.action.openSettings', 'aais');
    }),
    
    vscode.commands.registerCommand('aais.toggleGovernance', async () => {
      const newValue = !config.governanceMode;
      await config.setGovernanceMode(newValue);
      vscode.window.showInformationMessage(`AAIS Governance Mode: ${newValue ? 'ON' : 'OFF'}`);
      chatProvider.refresh();
    }),
    
    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('aais')) {
        config.reload();
        backendManager.updateConfig(config);
        chatProvider.refresh();
      }
    })
  );

  vscode.window.showInformationMessage('AAIS Coding Assistant activated');
}

export function deactivate() {
  backendManager?.dispose();
}