# AWS Amplify Gen 2 — Operator Console Auth & Trust Projection (Spike)

Optional **AWS-native** identity + GraphQL read model for the governed Operator Console
(`frontend/` React/Vite app). Python AAIS runtime and JSONL operator receipts stay the
**write authority** — same projection law as `deploy/firebase-data-connect/` and
`deploy/appwrite/`.

This spike was produced with the **AWS Amplify Cursor plugin** (`amplify-workflow` skill).

## Why this fits AAIS

| AAIS law | How this spike respects it |
|---|---|
| Humans hold final authority | Cognito `operator` group gates mutations; `observer` is read-only |
| Trust bundles are inspectable | `TrustBundleProjection` stores claim label + proof link + ledger hash anchor |
| Disagreements are logged | `GovernanceDeltaReceipt` captures human override + optional debt ticket |
| Query projection only | AppSync models are mirrors; `src/operator_decision_ledger.py` stays canonical |
| Testable before admission | Deploy sandbox first; wire frontend only after law filter passes |

## Layout

```
deploy/amplify/
├── README.md
├── package.json
├── tsconfig.json
└── amplify/
    ├── backend.ts
    ├── auth/resource.ts      # Cognito: operator | observer groups
    └── data/resource.ts      # TrustBundleProjection, GovernanceDeltaReceipt
```

## Prerequisites (plugin workflow)

| Check | This workspace |
|---|---|
| Node.js >= 18 | Present (`node -v`) |
| npm | Install Node.js npm component or use `corepack enable` |
| AWS CLI + credentials | **Not configured** — required before `ampx sandbox` |
| `aws-mcp` MCP server | **Not connected in Cursor** — enable plugin `.mcp.json` for SOP-guided deploy |

Setup guide: https://docs.amplify.aws/react/start/account-setup/

## Sandbox deploy (detailed)

### 1. Install tooling

**Windows (PowerShell as Administrator):**

```powershell
winget install Amazon.AWSCLI
```

Or download the AWS CLI MSI from https://aws.amazon.com/cli/

Verify:

```powershell
aws --version
node -v
npm -v
```

Use the full npm path if `npm` is not on PATH:

```powershell
& "C:\Program Files\nodejs\npm.cmd" -v
```

### 2. Configure AWS credentials

Create an IAM user or use SSO with permission to create Cognito, AppSync, CloudFormation, and IAM roles (Amplify Gen 2 sandbox uses CDK under the hood).

```powershell
aws configure
# AWS Access Key ID
# AWS Secret Access Key
# Default region name: us-east-1  (or your preferred region)
# Default output format: json
```

Confirm identity:

```powershell
aws sts get-caller-identity
```

Optional: copy `deploy/amplify/.env.example` to `deploy/amplify/.env` and set `AWS_PROFILE` / `AWS_REGION` if you use named profiles.

### 3. Deploy the Amplify sandbox

From repo root:

```powershell
cd deploy/amplify
npm install
npx ampx sandbox
```

Leave `ampx sandbox` running in its terminal. First deploy typically takes several minutes. It provisions:

- Cognito User Pool (email login)
- Groups: `operator`, `observer`
- AppSync API + DynamoDB tables for projection models

When the sandbox is healthy, open a **second terminal** in the same directory and generate frontend outputs:

```powershell
npx ampx generate outputs --out-dir ../../frontend/src
```

This writes `frontend/src/amplify_outputs.json` (gitignored). Restart the Vite dev server after generating outputs.

### 4. Create the first Cognito user

Sign-up is hidden in the UI (`hideSignUp` on the Authenticator). Create users via AWS Console or CLI:

**Console:** Cognito → User pools → your sandbox pool → Users → Create user → set email + temporary password.

**CLI** (replace pool id from `amplify_outputs.json` → `auth.user_pool_id`):

```powershell
aws cognito-idp admin-create-user `
  --user-pool-id us-east-1_XXXXX `
  --username operator@example.com `
  --user-attributes Name=email,Value=operator@example.com Name=email_verified,Value=true `
  --temporary-password "TempPass123!" `
  --message-action SUPPRESS
```

Assign a group:

```powershell
aws cognito-idp admin-add-user-to-group `
  --user-pool-id us-east-1_XXXXX `
  --username operator@example.com `
  --group-name operator
```

On first sign-in at `/auth/sign-in`, Cognito prompts for a new password.

### 5. Enable Cognito auth in the frontend

```powershell
cd ../../frontend
npm install
```

Create `frontend/.env.local`:

```env
VITE_AMPLIFY_AUTH=1
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the app:

```powershell
npm run dev
```

Open http://localhost:3000/auth/sign-in, sign in, then visit `/operator`. With `VITE_AMPLIFY_AUTH=1`, Operator and Platform routes redirect here when no JWT is present.

### 6. Smoke checklist

| Step | Expected |
|---|---|
| `/auth/sign-in` loads Authenticator | Email + password form |
| Sign in with Cognito user | Redirect to `/operator` (or prior route) |
| Browser devtools → Network → `/api/operator/*` | `Authorization: Bearer eyJ…` (Cognito access token) |
| Sign out (Cognito session cleared) | Operator routes redirect back to sign-in |

**Note:** Python API JWT validation is not wired yet. The frontend sends Cognito tokens; the backend may still accept unauthenticated or legacy API-key traffic until JWKS validation is added.

### 7. Tear down sandbox

Stop the `ampx sandbox` process (Ctrl+C). To delete cloud resources:

```powershell
npx ampx sandbox delete
```

### Troubleshooting

| Symptom | Fix |
|---|---|
| `aws: command not found` | Install AWS CLI; reopen terminal |
| `Could not load credentials` | Run `aws configure` or set `AWS_PROFILE` |
| `amplify_outputs.json` missing | Run `npx ampx generate outputs` while sandbox is up |
| Bootstrap warning, legacy auth fallback | Outputs file missing or invalid; regenerate |
| Sign-in works but API 401 | Backend does not validate Cognito JWT yet (expected for spike) |
| User cannot sign up in UI | By design — create users in Cognito Console/CLI |

## Setup (quick reference)

From `deploy/amplify/`:

```bash
npm install
npx ampx sandbox
npx ampx generate outputs --out-dir ../../frontend/src
```

Then in `frontend/`:

```bash
npm install
```

Copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_AMPLIFY_AUTH=1`.

## Runtime wiring (frontend bootstrap)

When `VITE_AMPLIFY_AUTH=1`, the app bootstraps Cognito before render:

| File | Role |
|---|---|
| `frontend/src/lib/bootstrapAuth.js` | Runs before `App` mount in `index.jsx` |
| `frontend/src/lib/amplifyAuth.js` | `Amplify.configure(outputs)`, session sync, Hub listener |
| `frontend/src/lib/auth.js` | `resolveAccessToken()` delegates to Cognito when flag is on |
| `frontend/src/lib/api.js` | Sends `Authorization: Bearer <cognito-jwt>`; refresh uses Amplify, not `/auth/refresh` |
| `frontend/src/pages/AmplifySignIn.jsx` | `/auth/sign-in` — Amplify UI Authenticator (email, sign-up hidden) |
| `frontend/src/components/AmplifyAuthGate.jsx` | Redirects `/operator/*` and `/platform/*` when no Cognito session |
| `frontend/src/amplify_outputs.json` | Generated by `ampx generate outputs` (gitignored) |

| Variable | Value | Effect |
|---|---|---|
| `VITE_AMPLIFY_AUTH` | `1` | Use Cognito JWT instead of custom `/auth/*` tokens |
| `VITE_API_BASE_URL` | existing Python API | Operator Console still hits `/api/operator/console` |
| Cognito group `operator` | assigned to human admins | Matches `operator_lanes` weight 1.0 |
| Cognito group `observer` | auditors / read-only seats | Matches console copy: "read-only evidence" |

Without `amplify_outputs.json`, bootstrap logs a warning and falls back to legacy localStorage auth.

Python would validate Cognito JWTs (JWKS) on operator routes — parallel to existing API-key path
in `platform/auth/api_keys.py` (**not implemented in this spike**).

## Law filter (pre-admission)

| Check | Result |
|---|---|
| Preserves doctrine | Yes — projection + auth boundary; ledger authority unchanged |
| Respects module purpose | Yes — serves Operator Console evidence surfaces |
| Testable | Pending — needs `ampx sandbox` + frontend smoke |
| Documentable | Yes — this README + schema |
| New seams | Yes — new deploy lane; requires admission doc like Scylla/Firebase |

**Status:** spike / not admitted. Do not point production traffic here until admission is documented.

## AWS Amplify MCP (recommended next step)

The Amplify plugin registers `aws-mcp` (`mcp-proxy-for-aws`). It is **not active in this
workspace yet** (available MCP servers: `user-twilio-docs`, `user-slack`, `user-figma`,
`user-vantage`).

Add the plugin MCP entry to Cursor settings, install AWS CLI, configure credentials, then
re-run the plugin's prerequisite check and sandbox deploy workflow.

Parallel references: [`deploy/firebase-data-connect/README.md`](../firebase-data-connect/README.md),
[`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](../../HUMAN_AI_CO_COLLABORATION_CHARTER.md),
[`docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md`](../../docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md).
