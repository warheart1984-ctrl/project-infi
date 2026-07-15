import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(scriptDir, '..');
const distRoot = path.join(siteRoot, 'dist');

const requiredPages = [
  'index.html',
  path.join('docs', 'overview.html'),
  path.join('docs', 'specifications', 'index.html'),
  path.join('docs', 'specifications', 'aaes-os-v1-implementation-slice.html'),
  path.join('docs', 'specifications', 'aaes-os-api-reference-stabilization.html'),
  path.join('docs', 'specifications', 'aaes-os-governance-traceability.html'),
  path.join('docs', 'specifications', 'aaes-os-example-path-cleanup.html'),
  path.join('docs', 'specifications', 'aaes-os-engineering-handbook.html'),
  path.join('docs', 'specifications', 'aaes-os-engineering-specification.html'),
  path.join('docs', 'specifications', 'aaes-os-engineering-standards.html'),
  path.join('docs', 'specifications', 'aaes-os-governance-specification.html'),
  path.join('docs', 'specifications', 'aaes-os-product-roadmap.html'),
  path.join('docs', 'veilthorn', 'index.html'),
  path.join('docs', 'veilthorn', 'quick-start.html'),
  path.join('docs', 'veilthorn', 'api-reference.html'),
  path.join('docs', 'veilthorn', 'proof-surface.html'),
  path.join('docs', 'veilthorn', 'examples.html'),
  path.join('docs', 'veilthorn', 'conformance.html'),
  path.join('docs', 'runtime', 'node-v0-1.html'),
  path.join('docs', 'ulx', 'ulx-ide-integration.html'),
  path.join('docs', 'visualizer', 'sovereign-ide.html'),
  path.join('docs', 'governance', 'crec.html'),
  path.join('docs', 'governance', 'constitutional-release-receipt.html'),
  path.join('docs', 'governance', 'constitutional-laws-of-intelligence.html'),
  path.join('docs', 'runtime', 'runtime-core.html'),
  path.join('docs', 'agents', 'aais-capabilities.html'),
  path.join('docs', 'agents', 'aais-routing-analytics.html'),
];

async function assertFileExists(relativePath) {
  const fullPath = path.join(distRoot, relativePath);
  await stat(fullPath);
  return fullPath;
}

async function main() {
  const indexPath = await assertFileExists('index.html');
  const indexHtml = await readFile(indexPath, 'utf8');

  if (!indexHtml.includes('AAES-OS Docs')) {
    throw new Error('Docs site smoke failed: homepage title is missing');
  }
  if (!indexHtml.includes('/docs/overview')) {
    throw new Error('Docs site smoke failed: homepage navigation does not link to the overview');
  }
  if (!indexHtml.includes('AAES-OS v1.x First Implementation Slice')) {
    throw new Error('Docs site smoke failed: homepage does not surface the first implementation slice');
  }
  if (!indexHtml.includes('AAES-OS API Reference Stabilization Slice')) {
    throw new Error('Docs site smoke failed: homepage does not surface the API reference stabilization slice');
  }
  if (!indexHtml.includes('Example path cleanup')) {
    throw new Error('Docs site smoke failed: homepage does not surface the example path cleanup slice');
  }
  if (!indexHtml.includes('ULX IDE integration map')) {
    throw new Error('Docs site smoke failed: homepage does not surface the ULX IDE integration map');
  }
  if (!indexHtml.includes('AAIS Capability Registry')) {
    throw new Error('Docs site smoke failed: homepage does not surface the AAIS registry');
  }

  for (const page of requiredPages.slice(1)) {
    await assertFileExists(page);
  }

  const specsIndexPath = path.join(distRoot, 'docs', 'specifications', 'index.html');
  const specsIndexHtml = await readFile(specsIndexPath, 'utf8');
  if (!specsIndexHtml.includes('AAES-OS v1.x First Implementation Slice')) {
    throw new Error('Docs site smoke failed: specifications index does not surface the first implementation slice');
  }
  if (!specsIndexHtml.includes('AAES-OS API Reference Stabilization Slice')) {
    throw new Error('Docs site smoke failed: specifications index does not surface the API reference stabilization slice');
  }
  if (!specsIndexHtml.includes('AAES-OS Example Path Cleanup Slice')) {
    throw new Error('Docs site smoke failed: specifications index does not surface the example path cleanup slice');
  }

  const ulxIntegrationPath = path.join(distRoot, 'docs', 'ulx', 'ulx-ide-integration.html');
  const ulxIntegrationHtml = await readFile(ulxIntegrationPath, 'utf8');
  if (!ulxIntegrationHtml.includes('ULX IDE Integration Map')) {
    throw new Error('Docs site smoke failed: ULX integration map page is missing');
  }
  if (!ulxIntegrationHtml.includes('ULX source editor')) {
    throw new Error('Docs site smoke failed: ULX integration map page does not surface the source editor');
  }

  const sovereignIdePath = path.join(distRoot, 'docs', 'visualizer', 'sovereign-ide.html');
  const sovereignIdeHtml = await readFile(sovereignIdePath, 'utf8');
  if (!sovereignIdeHtml.includes('ULX source editor, action buttons, selection mirror, shared source snapshot, and evidence receipt')) {
    throw new Error('Docs site smoke failed: Sovereign IDE visualizer does not surface the ULX source editor');
  }

  const aaisCapabilitiesPath = path.join(distRoot, 'docs', 'agents', 'aais-capabilities.html');
  const aaisCapabilitiesHtml = await readFile(aaisCapabilitiesPath, 'utf8');
  if (!aaisCapabilitiesHtml.includes('Constitutional Routing Hints')) {
    throw new Error('Docs site smoke failed: AAIS capability registry does not surface routing hints');
  }
  if (!aaisCapabilitiesHtml.includes('Live Capability Provenance')) {
    throw new Error('Docs site smoke failed: AAIS capability registry does not surface provenance');
  }
  if (!aaisCapabilitiesHtml.includes('AAIS -&gt; SovereignX -&gt; Engine Provenance (JSON View)')) {
    throw new Error('Docs site smoke failed: AAIS capability registry does not surface the provenance JSON view');
  }
  if (!aaisCapabilitiesHtml.includes('AAIS Coding Capability Registry')) {
    throw new Error('Docs site smoke failed: AAIS capability registry does not surface the coding capability registry');
  }
  if (!aaisCapabilitiesHtml.includes('Coding Provenance Graph')) {
    throw new Error('Docs site smoke failed: AAIS capability registry does not surface the coding provenance graph');
  }

  const analyticsPath = path.join(distRoot, 'docs', 'agents', 'aais-routing-analytics.html');
  const analyticsHtml = await readFile(analyticsPath, 'utf8');
  if (!analyticsHtml.includes('AAIS Routing Analytics')) {
    throw new Error('Docs site smoke failed: AAIS routing analytics page is missing');
  }

  console.log(`Docs site smoke passed: ${requiredPages.length} pages verified in ${distRoot}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
