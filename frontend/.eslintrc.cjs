module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  ignorePatterns: ["dist", "node_modules", ".eslintrc.cjs", "playwright.config.ts"],
  plugins: ["react-refresh"],
  rules: {
    // We intentionally co-locate the `useAuth` hook with its provider; the
    // Fast-Refresh-only rule is a dev-experience hint, not a correctness rule.
    "react-refresh/only-export-components": "off",
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  },
};
