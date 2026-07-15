#!/usr/bin/env tsx

import { createApp } from './server.js';

const PORT = Number(process.env.SOVEREIGN_CONTROL_PLANE_PORT ?? 4110);
const app = createApp();

app.listen(PORT, () => {
  console.log(`Sovereign Control Plane listening on http://localhost:${PORT}`);
});
