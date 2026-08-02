import * as vscode from 'vscode';

export class AAISConfig {
  private config: vscode.WorkspaceConfiguration;

  constructor() {
    this.config = vscode.workspace.getConfiguration('aais');
  }

  reload(): void {
    this.config = vscode.workspace.getConfiguration('aais');
  }

  get governanceMode(): boolean {
    return this.config.get('governanceMode', true);
  }

  async setGovernanceMode(value: boolean): Promise<void> {
    await this.config.update('governanceMode', value, vscode.ConfigurationTarget.Global);
    this.reload();
  }

  get preferredBackend(): string {
    return this.config.get('preferredBackend', 'auto');
  }

  async setPreferredBackend(value: string): Promise<void> {
    await this.config.update('preferredBackend', value, vscode.ConfigurationTarget.Global);
    this.reload();
  }

  get ollamaUrl(): string {
    return this.config.get('ollamaUrl', 'http://127.0.0.1:11434');
  }

  get autoDetect(): boolean {
    return this.config.get('autoDetect', true);
  }

  getGroqApiKey(): string | undefined {
    return process.env.GROQ_API_KEY;
  }

  getOpenRouterApiKey(): string | undefined {
    return process.env.OPENROUTER_API_KEY;
  }

  getCursorApiKey(): string | undefined {
    return process.env.CURSOR_API_KEY;
  }
}