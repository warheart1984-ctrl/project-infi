import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "nova-sdk": path.resolve(__dirname, "../agent/index.ts"),
    },
  },
  optimizeDeps: {
    exclude: ["nova-sdk"],
  },
  server: {
    port: 5173,
  },
});
