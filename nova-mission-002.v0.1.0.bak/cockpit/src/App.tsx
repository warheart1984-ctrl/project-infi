import { useEffect } from "react";
import { NovaShell } from "./NovaShell";
import { initializeNovaEventBridge, teardownNovaEventBridge } from "./state/NovaEventBridge";
import { connectClusterBridge, disconnectClusterBridge } from "./bridge/WebSocketBridge";
import "./styles/variables.css";

export function App() {
  useEffect(() => {
    void initializeNovaEventBridge();
    connectClusterBridge();
    return () => {
      teardownNovaEventBridge();
      disconnectClusterBridge();
    };
  }, []);

  return <NovaShell />;
}
