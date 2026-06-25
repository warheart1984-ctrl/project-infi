/// <reference types="svelte" />
/// <reference types="vite/client" />

interface OperatorConfig {
  kernelUrl?: string;
  lawfulBrainUrl?: string;
}

interface Window {
  __OPERATOR_CONFIG__?: OperatorConfig;
}
