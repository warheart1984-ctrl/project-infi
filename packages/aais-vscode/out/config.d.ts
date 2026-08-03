export declare class AAISConfig {
    private config;
    constructor();
    reload(): void;
    get governanceMode(): boolean;
    setGovernanceMode(value: boolean): Promise<void>;
    get preferredBackend(): string;
    setPreferredBackend(value: string): Promise<void>;
    get ollamaUrl(): string;
    get autoDetect(): boolean;
    getGroqApiKey(): string | undefined;
    getOpenRouterApiKey(): string | undefined;
    getCursorApiKey(): string | undefined;
}
//# sourceMappingURL=config.d.ts.map