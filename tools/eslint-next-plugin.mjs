const noopRule = {
  meta: {
    type: "problem",
    docs: {
      recommended: false
    },
    schema: []
  },
  create() {
    return {};
  }
};

const rules = {
  "google-font-display": noopRule,
  "google-font-preconnect": noopRule,
  "next-script-for-ga": noopRule,
  "no-assign-module-variable": noopRule,
  "no-async-client-component": noopRule,
  "no-before-interactive-script-outside-document": noopRule,
  "no-css-tags": noopRule,
  "no-document-import-in-page": noopRule,
  "no-duplicate-head": noopRule,
  "no-head-element": noopRule,
  "no-head-import-in-document": noopRule,
  "no-html-link-for-pages": noopRule,
  "no-img-element": noopRule,
  "no-page-custom-font": noopRule,
  "no-script-component-in-head": noopRule,
  "no-styled-jsx-in-document": noopRule,
  "no-sync-scripts": noopRule,
  "no-title-in-document-head": noopRule,
  "no-typos": noopRule,
  "no-unwanted-polyfillio": noopRule
};

const recommendedRules = {
  "@next/next/google-font-display": "warn",
  "@next/next/google-font-preconnect": "warn",
  "@next/next/next-script-for-ga": "warn",
  "@next/next/no-assign-module-variable": "warn",
  "@next/next/no-async-client-component": "warn",
  "@next/next/no-before-interactive-script-outside-document": "warn",
  "@next/next/no-css-tags": "warn",
  "@next/next/no-document-import-in-page": "error",
  "@next/next/no-duplicate-head": "error",
  "@next/next/no-head-element": "warn",
  "@next/next/no-head-import-in-document": "error",
  "@next/next/no-html-link-for-pages": "warn",
  "@next/next/no-img-element": "warn",
  "@next/next/no-page-custom-font": "warn",
  "@next/next/no-script-component-in-head": "error",
  "@next/next/no-styled-jsx-in-document": "warn",
  "@next/next/no-sync-scripts": "warn",
  "@next/next/no-title-in-document-head": "warn",
  "@next/next/no-typos": "warn",
  "@next/next/no-unwanted-polyfillio": "warn"
};

const coreWebVitalsRules = {
  "@next/next/no-html-link-for-pages": "error",
  "@next/next/no-sync-scripts": "error"
};

export default {
  meta: {
    name: "@next/eslint-plugin-next",
    version: "local-flat-config-compat"
  },
  rules,
  configs: {
    recommended: {
      plugins: ["@next/next"],
      rules: recommendedRules
    },
    "core-web-vitals": {
      plugins: ["@next/next"],
      rules: coreWebVitalsRules
    }
  }
};
