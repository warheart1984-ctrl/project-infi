import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import nextPlugin from "./tools/eslint-next-plugin.mjs";

const workspaceFiles = [
  "packages/**/*.{js,jsx,ts,tsx,mjs,cjs}",
  "services/**/*.{js,jsx,ts,tsx,mjs,cjs}"
];

export default tseslint.config(
  {
    ignores: [
      "**/dist/**",
      "**/dist-smoke/**",
      "**/build/**",
      "**/coverage/**",
      "**/node_modules/**",
      "**/.cache/**",
      "**/.docusaurus/**",
      "**/.vite/**",
      "**/.next/**",
      "**/next-env.d.ts"
    ]
  },
  {
    files: workspaceFiles,
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node
      }
    },
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-undef": "off"
    }
  },
  {
    files: ["services/platform-web/**/*.{js,jsx,ts,tsx,mjs,cjs}", "services/platform-web/package.json"],
    plugins: {
      "@next/next": nextPlugin
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules
    },
    settings: {
      next: {
        rootDir: "services/platform-web"
      }
    }
  }
);
