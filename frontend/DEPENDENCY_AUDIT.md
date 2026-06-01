# Frontend Dependency Audit

Last checked: 2026-04-08

## Current state

- The frontend now runs on `Vite 6` with `Vitest 3`.
- Direct runtime dependencies are installable and healthy.
- `axios` has been updated to `1.15.0`.
- `npm audit --omit=dev` reports `0` production vulnerabilities.
- `npm test -- --coverage --watchAll=false` passes.
- `npm run build` passes.

## Audit summary

`npm audit --omit=dev` is now clean after removing the Create React App toolchain.

Development dependencies should still be monitored, but the previous runtime security debt from
`react-scripts`, `webpack-dev-server`, and related transitive packages has been removed.

## Safe actions completed

- migrated the frontend from `react-scripts` to `Vite`
- preserved the existing `npm start`, `npm run build`, and `npm test -- --coverage --watchAll=false` command flow
- kept the production build output in `build/`
- added `npm run test:ci`
- added `npm run lint`
- added `npm run audit:prod`
- verified the current app still builds, lints, and tests cleanly

## Recommended next step

The next improvement is performance-focused rather than security-focused:

1. Keep splitting route-heavy screens so the first load bundle stays small.
2. Add a browser smoke test around the workflow routes.
3. Expand Vitest coverage around settings, builder validation, and run polling.
4. Then consider targeted React ecosystem upgrades in a separate pass.

## What not to do

Avoid bulk dependency upgrades without rerunning the workflow UI smoke path.
The remaining risk is now behavioral drift, not hidden CRA transitive vulnerabilities.
