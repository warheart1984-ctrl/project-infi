import { AAISConfig } from './config';
export declare class AAISBackendManager {
    private stack;
    private config;
    constructor(config: AAISConfig);
    initialize(): Promise<void>;
    updateConfig(config: AAISConfig): void;
    getStack(): Promise<import("@aaes-os/coding-assistant").FreeCodingStack>;
    getAvailableBackends(): string[];
    getSkippedBackends(): Array<{
        name: string;
        reason: string;
    }>;
    dispose(): void;
}
//# sourceMappingURL=backendManager.d.ts.map