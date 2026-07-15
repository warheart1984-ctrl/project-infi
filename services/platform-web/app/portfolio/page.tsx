import styles from './portfolio.module.css';

const repositories = [
  { name: 'Project INFI', tier: 'Verified prototype', build: 'Pass', test: '435/435', coverage: 'Partial', security: 'Baseline', docs: 'Strong', release: 'Signed P2', deploy: 'Local', production: 'Not ready' },
  { name: 'ULX', tier: 'Advanced prototype', build: 'Pass', test: '11/11 targeted', coverage: 'Gap', security: 'Designed', docs: 'Strong', release: 'Evidence package', deploy: 'Local', production: 'Not ready' },
  { name: 'PARAGON One', tier: 'Prototype', build: 'Not defined', test: '9/9', coverage: 'Gap', security: 'Baseline', docs: 'Standardized', release: 'Local receipt', deploy: 'Local', production: 'Not ready' },
  { name: 'Agentic Coding Agent', tier: 'Verified slice', build: 'Pass', test: '2/2', coverage: 'Gap', security: 'Baseline', docs: 'Standardized', release: 'Local receipt', deploy: 'Local', production: 'Not ready' },
  { name: 'SkillzMcGee', tier: 'Verified slice', build: 'Recorded pass', test: 'Recorded pass', coverage: 'Partial', security: 'Partial', docs: 'Strong', release: 'Partial', deploy: 'Local', production: 'Not ready' },
];

const metrics = [
  ['5', 'tracked repositories'],
  ['4', 'fresh local build/test baselines'],
  ['0', 'production-certified repositories'],
  ['25/25', 'INFI replay/drift tests'],
];

function statusClass(value: string) {
  if (/pass|signed|standardized|strong|\d+\/\d+/i.test(value) && !/partial/i.test(value)) return styles.good;
  if (/gap|not ready|not defined/i.test(value)) return styles.blocked;
  return styles.partial;
}

export default function PortfolioEngineeringDashboard() {
  return (
    <main className={styles.page}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>CONSTITUTIONAL RUNTIME · ENGINEERING HEALTH</p>
          <h1>Foundation readiness, without inflated claims.</h1>
          <p className={styles.lede}>One evidence model for build, test, coverage, security, documentation, release, deployment, and production readiness.</p>
        </div>
        <div className={styles.freeze}><span>ARCHITECTURAL FREEZE</span><strong>Runtime v1.0</strong><small>Execution over expansion</small></div>
      </header>

      <section className={styles.metrics} aria-label="Portfolio summary">
        {metrics.map(([value, label]) => <article key={label}><strong>{value}</strong><span>{label}</span></article>)}
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><p className={styles.eyebrow}>PORTFOLIO MATRIX</p><h2>Repository readiness</h2></div><p>Verified 14 July 2026</p></div>
        <div className={styles.tableWrap}>
          <table>
            <thead><tr><th>Repository</th><th>Build</th><th>Tests</th><th>Coverage</th><th>Security</th><th>Docs</th><th>Release</th><th>Deploy</th><th>Production</th></tr></thead>
            <tbody>{repositories.map((repo) => <tr key={repo.name}><th><strong>{repo.name}</strong><span>{repo.tier}</span></th>{(['build','test','coverage','security','docs','release','deploy','production'] as const).map((key) => <td key={key}><span className={`${styles.status} ${statusClass(repo[key])}`}>{repo[key]}</span></td>)}</tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className={styles.grid}>
        <article className={styles.panel}><p className={styles.eyebrow}>FROZEN EXECUTION LOOP</p><h2>Authority stays in the loop</h2><ol className={styles.loop}>{['Intent','Planning (ISL)','Governance (CIEMS)','Authorized execution','Evidence','Reflection','State (USS)','Learning'].map((item, index) => <li key={item}><span>{String(index + 1).padStart(2,'0')}</span>{item}</li>)}</ol></article>
        <article className={styles.panel}><p className={styles.eyebrow}>NEXT RELEASE GATE</p><h2>What blocks production</h2><ul className={styles.blockers}><li>Add measured coverage thresholds.</li><li>Run dependency, secrets, static, and adversarial security checks.</li><li>Capture load, latency, endurance, and resource benchmarks.</li><li>Deploy to a production-like environment with rollback evidence.</li><li>Obtain independent reviewer attestation.</li></ul></article>
      </section>
    </main>
  );
}
