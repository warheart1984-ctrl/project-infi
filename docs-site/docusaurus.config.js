export default {
  title: 'AAES-OS Docs',
  tagline: 'Governed runtime, evidence, and constitutional readiness',
  url: 'http://localhost',
  baseUrl: '/',
  favicon: 'img/logo.svg',
  organizationName: 'aaes-os',
  projectName: 'docs-site',
  onBrokenLinks: 'throw',
  presets: [
    [
      'classic',
      {
        debug: false,
        docs: {
          sidebarPath: './sidebars.js',
        },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'AAES-OS Docs',
      items: [
        { to: '/docs/overview', label: 'Overview', position: 'left' },
        { to: '/docs/governance/constitutional-laws-of-intelligence', label: 'Constitution', position: 'left' },
        { to: '/docs/governance/doctrine', label: 'Governance', position: 'left' },
        { to: '/docs/specifications', label: 'Specifications', position: 'left' },
        { to: '/docs/runtime/runtime-core', label: 'Runtime', position: 'left' },
        {
          label: 'Live Surfaces',
          position: 'left',
          items: [
            { to: '/docs/runtime/live-surfaces', label: 'Live Surfaces' },
            { to: '/docs/runtime/coda-doc', label: 'CodaDoc' },
            { to: '/docs/runtime/coda-runtime', label: 'CodaRuntime' },
            { to: '/docs/runtime/nova-coda', label: 'NovaCoda' },
            { to: '/docs/runtime/nova-substrate-client', label: 'Nova Substrate Client' },
            { to: '/docs/runtime/isl-runtime', label: 'ISL Runtime' },
            { to: '/docs/runtime/gcre-sysmin', label: 'GCRE-SYSMIN-001' },
          ],
        },
        {
          label: 'Visualizers',
          position: 'left',
          items: [
            { to: '/docs/visualizer/governance-dashboard', label: 'Governance Dashboard' },
            { to: '/docs/visualizer/sovereign-ide', label: 'Sovereign IDE' },
          ],
        },
        { to: '/docs/runtime/node-v0-1', label: 'Node v0.1', position: 'left' },
        { to: '/docs/veilthorn', label: 'VEILTHORN', position: 'left' },
        { to: '/docs/agents/infinity-agents', label: 'Agents', position: 'left' },
        { to: '/docs/ulx/ulx-language', label: 'ULX', position: 'left' },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Overview', to: '/docs/overview' },
            { label: 'Constitution', to: '/docs/governance/constitutional-laws-of-intelligence' },
            { label: 'Governance', to: '/docs/governance/doctrine' },
            { label: 'Specifications', to: '/docs/specifications' },
            { label: 'Runtime', to: '/docs/runtime/runtime-core' },
            { label: 'Live Surfaces', to: '/docs/runtime/live-surfaces' },
            { label: 'Visualizers', to: '/docs/visualizer/sovereign-ide' },
            { label: 'Node v0.1', to: '/docs/runtime/node-v0-1' },
            { label: 'VEILTHORN', to: '/docs/veilthorn' },
          ],
        },
        {
          title: 'Systems',
          items: [
            { label: 'Agents', to: '/docs/agents/infinity-agents' },
            { label: 'ULX', to: '/docs/ulx/ulx-language' },
            { label: 'Lifecycle', to: '/docs/runtime-lifecycle/boot-sequence' },
          ],
        },
      ],
      copyright: `Copyright (c) ${new Date().getFullYear()} AAES-OS.`,
    },
  },
};
