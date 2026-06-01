import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { setPlatformApiKey, getPlatformApiBaseUrl } from '../lib/platformApi';
import './PlatformConsole.css';

const EXAMPLES = [
  { name: 'Mechanic scan', path: 'docs/subsystems/platform/examples/mechanic_scan.json' },
  { name: 'Slingshot preload', path: 'docs/subsystems/platform/examples/slingshot_preload.json' },
  { name: 'Lab session', path: 'docs/subsystems/platform/examples/lab_session.json' },
];

export default function PlatformGettingStarted() {
  const [key, setKey] = useState('');
  const [org, setOrg] = useState('acme');

  const save = () => {
    setPlatformApiKey(key.trim());
    localStorage.setItem('platform_active_org', org);
  };

  const curlJob = `curl -X POST ${getPlatformApiBaseUrl()}/v1/jobs \\
  -H "X-Api-Key: YOUR_KEY" -H "Content-Type: application/json" \\
  -d '{"subsystem":"mechanic","kind":"mechanic.scan","params":{"case_id":"demo","repo_path":"mechanic/fixtures/sample-customer-repo"}}'`;

  return (
    <div className="platform-console">
      <h1>Platform Getting Started</h1>
      <p>API: {getPlatformApiBaseUrl()}</p>
      <div className="platform-console__controls">
        <input placeholder="API key" value={key} onChange={(e) => setKey(e.target.value)} />
        <input placeholder="org_id" value={org} onChange={(e) => setOrg(e.target.value)} />
        <button type="button" onClick={save}>Save</button>
      </div>
      <pre className="platform-console__pre">{curlJob}</pre>
      <h3>Example payloads</h3>
      <ul>
        {EXAMPLES.map((ex) => (
          <li key={ex.name}>{ex.name} — <code>{ex.path}</code></li>
        ))}
      </ul>
      <p><Link to="/platform">Open Platform Ops →</Link></p>
    </div>
  );
}
