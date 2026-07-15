# AAIS Google Drive Connector

Status: Implemented; requires local Google OAuth client secret.

## Google Cloud configuration

1. Enable the Google Drive API.
2. Configure the OAuth consent screen and add the `drive.file` scope.
3. Create an OAuth 2.0 Web application client.
4. Register the exact redirect URI used by your local web port. The dedicated launcher defaults to:

   `http://localhost:3001/api/integrations/google-drive/callback`

5. Store the client ID and secret in the ignored root `.env` file.

The connector requests offline access and explicit consent so Google returns a refresh token. Refresh tokens are AES-256-GCM encrypted in `.local/google-drive/tokens.json`; the encryption key remains in `.env`.

## Start

Because this workstation already uses ports 3000 and 4100, start the dedicated integration stack on 3001 and 4101:

```powershell
.\scripts\start-google-drive-stack.ps1
```

Open `http://localhost:3001/integrations/google-drive`, sign into AAIS, and select **Connect Google Drive**.

## Access model

The default `drive.file` scope permits AAIS to manage files it creates and files explicitly opened or shared with the application. It does not grant unrestricted access to the entire Drive. Broader scopes require an explicit governance decision and may trigger Google verification requirements.

## Governed operations

The connector supports connection status, disconnect, file listing, metadata lookup, and text-file creation. Each Drive operation returns an evidence receipt containing the actor, operation, timestamp, file identifier when applicable, and request/response digests. Secrets and file contents are never included in receipts.
