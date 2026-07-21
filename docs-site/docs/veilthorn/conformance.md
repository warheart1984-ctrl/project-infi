# Conformance

VEILTHORN Stage 1 conforms when the docs layer is complete, the routes resolve, and the smoke test passes.

## Conformance requirements

- The VEILTHORN landing page exists and is reachable from the docs navigation
- The quick start, API reference, proof surface, examples, and conformance pages are all present
- The Node v0.1 page exists as a document-only reference artifact
- The generated HTML pages are present after a docs build
- The docs homepage links to VEILTHORN and the reference artifact
- Stage 1 does not claim Stage 2 runtime behavior

## Smoke expectation

Run:

```bash
npm run verify
```

The verification step should rebuild the site and confirm that the generated HTML pages for the VEILTHORN docs and the Node v0.1 page exist.

## Non-conformance

The slice does not conform if any of the following are true:

- the VEILTHORN docs are missing from the sidebar or navigation
- the canonical inference path is absent
- the proof surface fields are not stated explicitly
- the docs imply that Stage 2 is already live

