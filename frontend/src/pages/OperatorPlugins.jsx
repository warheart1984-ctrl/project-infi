import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

function OperatorPlugins() {
  const [tab, setTab] = useState('libraries');
  const [libraries, setLibraries] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [organs, setOrgans] = useState([]);
  const [mesh, setMesh] = useState(null);
  const [meshPlan, setMeshPlan] = useState(null);
  const [meshIntent, setMeshIntent] = useState('research brief creative workflow');
  const [culture, setCulture] = useState(null);
  const [cultureCandidates, setCultureCandidates] = useState([]);
  const [identity, setIdentity] = useState(null);
  const [identityCandidates, setIdentityCandidates] = useState([]);
  const [narrative, setNarrative] = useState(null);
  const [narrativeCandidates, setNarrativeCandidates] = useState([]);
  const [autobiographical, setAutobiographical] = useState(null);
  const [autobiographicalCandidates, setAutobiographicalCandidates] = useState([]);
  const [social, setSocial] = useState(null);
  const [socialCandidates, setSocialCandidates] = useState([]);
  const [multiBeing, setMultiBeing] = useState(null);
  const [multiBeingCandidates, setMultiBeingCandidates] = useState([]);
  const [cultureOfBeings, setCultureOfBeings] = useState(null);
  const [cultureOfBeingsCandidates, setCultureOfBeingsCandidates] = useState([]);
  const [ecosystems, setEcosystems] = useState(null);
  const [ecosystemCandidates, setEcosystemCandidates] = useState([]);
  const [governanceMembrane, setGovernanceMembrane] = useState(null);
  const [membraneCandidates, setMembraneCandidates] = useState([]);
  const [diplomacy, setDiplomacy] = useState(null);
  const [diplomacyCandidates, setDiplomacyCandidates] = useState([]);
  const [normFederations, setNormFederations] = useState(null);
  const [normFederationCandidates, setNormFederationCandidates] = useState([]);
  const [constitutionalEvolution, setConstitutionalEvolution] = useState(null);
  const [amendmentCandidates, setAmendmentCandidates] = useState([]);
  const [civilizations, setCivilizations] = useState(null);
  const [civilizationCandidates, setCivilizationCandidates] = useState([]);
  const [plugins, setPlugins] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chainId, setChainId] = useState('research_brief');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [libRes, wfRes, organRes, plugRes, meshRes, cultureRes, identityRes, narrativeRes, autobiographicalRes, socialRes, multiBeingRes, cobRes, ecoRes, mgmRes, dipRes, nfdRes, cevRes, gcvRes] = await Promise.all([
        apiGet('/api/operator/plugins/libraries'),
        apiGet('/api/operator/plugins/workflows'),
        apiGet('/api/operator/organs'),
        apiGet('/api/operator/plugins'),
        apiGet('/api/operator/organs/mesh'),
        apiGet('/api/operator/culture'),
        apiGet('/api/operator/identity'),
        apiGet('/api/operator/narrative'),
        apiGet('/api/operator/autobiographical'),
        apiGet('/api/operator/social'),
        apiGet('/api/operator/multi-being'),
        apiGet('/api/operator/culture-of-beings'),
        apiGet('/api/operator/ecosystems'),
        apiGet('/api/operator/governance-membrane'),
        apiGet('/api/operator/diplomacy'),
        apiGet('/api/operator/norm-federations'),
        apiGet('/api/operator/constitutional-evolution'),
        apiGet('/api/operator/civilizations'),
      ]);
      setLibraries(libRes.data?.libraries || []);
      setWorkflows(wfRes.data?.workflows || []);
      setOrgans(organRes.data?.organs || []);
      setPlugins(plugRes.data?.plugins || null);
      setMesh(meshRes.data || null);
      setCulture(cultureRes.data || null);
      setCultureCandidates(cultureRes.data?.recent_candidates || []);
      setIdentity(identityRes.data || null);
      setIdentityCandidates(identityRes.data?.recent_candidates || []);
      setNarrative(narrativeRes.data || null);
      setNarrativeCandidates(narrativeRes.data?.recent_candidates || []);
      setAutobiographical(autobiographicalRes.data || null);
      setAutobiographicalCandidates(autobiographicalRes.data?.recent_candidates || []);
      setSocial(socialRes.data || null);
      setSocialCandidates(socialRes.data?.recent_candidates || []);
      setMultiBeing(multiBeingRes.data || null);
      setMultiBeingCandidates(multiBeingRes.data?.recent_candidates || []);
      setCultureOfBeings(cobRes.data || null);
      setCultureOfBeingsCandidates(cobRes.data?.recent_candidates || []);
      setEcosystems(ecoRes.data || null);
      setEcosystemCandidates(ecoRes.data?.recent_candidates || []);
      setGovernanceMembrane(mgmRes.data || null);
      setMembraneCandidates(mgmRes.data?.recent_candidates || []);
      setDiplomacy(dipRes.data || null);
      setDiplomacyCandidates(dipRes.data?.recent_candidates || []);
      setNormFederations(nfdRes.data || null);
      setNormFederationCandidates(nfdRes.data?.recent_candidates || []);
      setConstitutionalEvolution(cevRes.data || null);
      setAmendmentCandidates(cevRes.data?.recent_candidates || []);
      setCivilizations(gcvRes.data || null);
      setCivilizationCandidates(gcvRes.data?.recent_candidates || []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load operator plugins.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const togglePlug = async (plugId, enabled) => {
    try {
      await apiPost(`/api/operator/plugins/${encodeURIComponent(plugId)}/enabled`, { enabled });
      await refresh();
      toast.success(enabled ? 'Plug enabled' : 'Plug disabled');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not toggle plug.'));
    }
  };

  const runChain = async () => {
    try {
      const res = await apiPost(`/api/operator/workflows/${encodeURIComponent(chainId)}/execute`, {
        operator_approved: true,
        dry_run: true,
        args: {},
      });
      toast.success(`Chain run: ${res.data?.run?.run_id || 'ok'}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Chain execution failed.'));
    }
  };

  const planMesh = async () => {
    try {
      const res = await apiPost('/api/operator/organs/mesh/plan', { intent_text: meshIntent });
      setMeshPlan(res.data?.plan || res.data);
      toast.success(`Mesh plan: ${res.data?.outcome || res.data?.plan?.outcome || 'ok'}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Mesh plan failed.'));
    }
  };

  const runMeshDry = async () => {
    try {
      const plan = meshPlan || (await apiPost('/api/operator/organs/mesh/plan', { intent_text: meshIntent })).data;
      const res = await apiPost('/api/operator/organs/mesh/runs', {
        plan: plan.plan || plan,
        operator_approved: true,
        dry_run: true,
      });
      toast.success(`Mesh run: ${res.data?.run_id || res.data?.run?.run_id || 'ok'}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Mesh run failed.'));
    }
  };

  const observeCulture = async () => {
    try {
      const res = await apiPost('/api/operator/culture/observe', { window_days: 30 });
      setCultureCandidates(res.data?.candidates || res.data?.observation?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} habit candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Culture observe failed.'));
    }
  };

  const adoptHabit = async (candidate) => {
    try {
      await apiPost('/api/operator/culture/habits/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Habit adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Habit adoption failed.'));
    }
  };

  const observeIdentity = async () => {
    try {
      const res = await apiPost('/api/operator/identity/observe', { window_days: 30 });
      setIdentityCandidates(res.data?.candidates || res.data?.observation?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} identity candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Identity observe failed.'));
    }
  };

  const adoptIdentityClaim = async (candidate) => {
    try {
      await apiPost('/api/operator/identity/claims/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Identity claim adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Identity claim adoption failed.'));
    }
  };

  const observeNarrative = async () => {
    try {
      const res = await apiPost('/api/operator/narrative/observe', { window_days: 30 });
      setNarrativeCandidates(res.data?.candidates || res.data?.observation?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} narrative candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Narrative observe failed.'));
    }
  };

  const adoptNarrativeBeat = async (candidate) => {
    try {
      await apiPost('/api/operator/narrative/beats/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Narrative beat adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Narrative beat adoption failed.'));
    }
  };

  const observeAutobiographical = async () => {
    try {
      const res = await apiPost('/api/operator/autobiographical/observe', { window_days: 30 });
      setAutobiographicalCandidates(res.data?.candidates || res.data?.observation?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} autobiographical candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Autobiographical observe failed.'));
    }
  };

  const adoptAutobiographicalEpisode = async (candidate) => {
    try {
      await apiPost('/api/operator/autobiographical/episodes/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Autobiographical episode adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Autobiographical episode adoption failed.'));
    }
  };

  const observeSocial = async () => {
    try {
      const res = await apiPost('/api/operator/social/observe', { window_days: 30 });
      setSocialCandidates(res.data?.candidates || res.data?.observation?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} social bond candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Social observe failed.'));
    }
  };

  const adoptSocialBond = async (candidate) => {
    try {
      await apiPost('/api/operator/social/bonds/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Social bond adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Social bond adoption failed.'));
    }
  };

  const observeMultiBeing = async () => {
    try {
      const res = await apiPost('/api/operator/multi-being/observe', { window_days: 30 });
      setMultiBeingCandidates(res.data?.candidates || res.data?.observation?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} multi-being pact candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Multi-being observe failed.'));
    }
  };

  const adoptMultiBeingPact = async (candidate) => {
    try {
      await apiPost('/api/operator/multi-being/pacts/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Multi-being pact adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Multi-being pact adoption failed.'));
    }
  };

  const observeCultureOfBeings = async () => {
    try {
      const res = await apiPost('/api/operator/culture-of-beings/observe', { window_days: 30 });
      setCultureOfBeingsCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} shared norm candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Culture-of-beings observe failed.'));
    }
  };

  const adoptSharedNorm = async (candidate) => {
    try {
      await apiPost('/api/operator/culture-of-beings/norms/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Shared norm adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Shared norm adoption failed.'));
    }
  };

  const observeEcosystems = async () => {
    try {
      const res = await apiPost('/api/operator/ecosystems/observe', { window_days: 30 });
      setEcosystemCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} charter candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Ecosystem observe failed.'));
    }
  };

  const adoptCharter = async (candidate) => {
    try {
      await apiPost('/api/operator/ecosystems/charters/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Ecosystem charter adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Charter adoption failed.'));
    }
  };

  const observeMembrane = async () => {
    try {
      const res = await apiPost('/api/operator/governance-membrane/observe', { window_days: 30 });
      setMembraneCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} membrane policy candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Membrane observe failed.'));
    }
  };

  const adoptMembranePolicy = async (candidate) => {
    try {
      await apiPost('/api/operator/governance-membrane/policies/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Membrane policy adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Membrane policy adoption failed.'));
    }
  };

  const observeDiplomacy = async () => {
    try {
      const res = await apiPost('/api/operator/diplomacy/observe', { window_days: 30 });
      setDiplomacyCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} diplomatic accord candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Diplomacy observe failed.'));
    }
  };

  const adoptDiplomaticAccord = async (candidate) => {
    try {
      await apiPost('/api/operator/diplomacy/accords/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Diplomatic accord adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Diplomatic accord adoption failed.'));
    }
  };

  const observeNormFederations = async () => {
    try {
      const res = await apiPost('/api/operator/norm-federations/observe', { window_days: 30 });
      setNormFederationCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} treaty candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Norm federation observe failed.'));
    }
  };

  const adoptNormFederationTreaty = async (candidate) => {
    try {
      await apiPost('/api/operator/norm-federations/treaties/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Norm federation treaty adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Treaty adoption failed.'));
    }
  };

  const observeConstitutionalEvolution = async () => {
    try {
      const res = await apiPost('/api/operator/constitutional-evolution/observe', { window_days: 30 });
      setAmendmentCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} amendment candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Constitutional evolution observe failed.'));
    }
  };

  const adoptCharterAmendment = async (candidate) => {
    try {
      await apiPost('/api/operator/constitutional-evolution/amendments/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Charter amendment adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Amendment adoption failed.'));
    }
  };

  const observeCivilizations = async () => {
    try {
      const res = await apiPost('/api/operator/civilizations/observe', { window_days: 30 });
      setCivilizationCandidates(res.data?.candidates || []);
      toast.success(`Observed ${res.data?.candidate_count ?? 0} civilization candidates`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Civilization observe failed.'));
    }
  };

  const adoptCivilizationCharter = async (candidate) => {
    try {
      await apiPost('/api/operator/civilizations/charters/adopt', { candidate, operator_approved: true });
      await refresh();
      toast.success('Civilization charter adopted');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Civilization adoption failed.'));
    }
  };

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Operator Plugins</h1>
        <p>Libraries, workflow bundles, organs, and governed chain execution.</p>
      </div>
      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/operator">Console</Link>
        <Link className="workflow-page-link" to="/operator/brain">Brain Sessions</Link>
        <Link className="workflow-page-link" to="/operator/ledger">Decision Ledger</Link>
        <button type="button" className="workflow-secondary-btn" onClick={refresh}>Refresh</button>
      </div>
      <div className="workflow-page-actions">
        {['libraries', 'workflows', 'organs', 'mesh', 'culture', 'identity', 'narrative', 'autobiographical', 'social', 'multi-being', 'culture-of-beings', 'ecosystems', 'membrane', 'diplomacy', 'norm-federations', 'constitutional-evolution', 'civilizations', 'chain'].map((t) => (
          <button key={t} type="button" className={`workflow-secondary-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading...</div>
      ) : (
        <>
          {tab === 'libraries' ? (
            <div className="workflow-approval-list">
              {libraries.map((lib) => (
                <article key={lib.identity?.library_id} className="workflow-card page-panel">
                  <strong>{lib.identity?.display_name}</strong>
                  <div className="workflow-step-type">{lib.identity?.library_class}</div>
                </article>
              ))}
            </div>
          ) : null}
          {tab === 'workflows' ? (
            <div className="workflow-approval-list">
              {workflows.map((wf) => (
                <article key={wf.workflow_id} className="workflow-card page-panel">
                  <strong>{wf.display_name}</strong>
                  <div className="workflow-step-type">{wf.workflow_id} · {wf.category}</div>
                </article>
              ))}
            </div>
          ) : null}
          {tab === 'organs' ? (
            <div className="workflow-approval-list">
              {organs.map((organ) => (
                <article key={organ.identity?.family_id} className="workflow-card page-panel">
                  <strong>{organ.identity?.display_name}</strong>
                  <div className="workflow-step-type">{organ.identity?.family_id}</div>
                </article>
              ))}
            </div>
          ) : null}
          {tab === 'mesh' ? (
            <div className="workflow-card page-panel">
              <p>Handoff edges: {mesh?.edge_count ?? '—'} · graph valid: {String(mesh?.graph_valid ?? false)}</p>
              <label>
                Intent
                <input value={meshIntent} onChange={(e) => setMeshIntent(e.target.value)} style={{ marginLeft: '0.5rem', width: '60%' }} />
              </label>
              <button type="button" className="workflow-secondary-btn" onClick={planMesh} style={{ marginLeft: '0.5rem' }}>
                Plan mesh (OCC-0)
              </button>
              <button type="button" className="workflow-secondary-btn" onClick={runMeshDry} style={{ marginLeft: '0.5rem' }}>
                Run mesh (dry-run)
              </button>
              {meshPlan ? (
                <pre style={{ marginTop: '1rem', fontSize: '0.85rem' }}>{JSON.stringify(meshPlan, null, 2)}</pre>
              ) : null}
            </div>
          ) : null}
          {tab === 'culture' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted: {culture?.posture?.adopted_habits ?? '—'} · candidates: {culture?.posture?.candidate_habits ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeCulture}>
                Observe habits (HCC-0)
              </button>
              <Link className="workflow-page-link" to="/operator/plugins" style={{ marginLeft: '0.5rem' }} onClick={() => setChainId('habit_review')}>
                habit_review chain
              </Link>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {cultureCandidates.map((c) => (
                  <article key={c.candidate_id || c.pattern_key} className="workflow-card page-panel">
                    <strong>{c.pattern_kind} · {c.pattern_key || c.candidate_id}</strong>
                    <div className="workflow-step-type">count={c.occurrence_count}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptHabit(c)}>
                      Adopt (HCC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'identity' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted: {identity?.posture?.adopted_claims ?? '—'} · candidates:{' '}
                {identity?.posture?.candidate_claims ?? '—'} · anchor aligned:{' '}
                {String(identity?.posture?.anchor_aligned ?? identity?.anchor?.authority_owner ?? '—')}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeIdentity}>
                Observe drift (ICC-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {identityCandidates.map((c) => (
                  <article key={c.candidate_id || c.claim_id} className="workflow-card page-panel">
                    <strong>{c.claim_kind} · {c.candidate_id || c.claim_id}</strong>
                    <div className="workflow-step-type">{c.statement?.slice(0, 120)}</div>
                    <div className="workflow-step-type">icc={c.icc_class} · anchor={String(c.anchor_alignment)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptIdentityClaim(c)}>
                      Adopt (ICC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'narrative' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted: {narrative?.posture?.adopted_beats ?? '—'} · candidates:{' '}
                {narrative?.posture?.candidate_beats ?? '—'} · continuity:{' '}
                {narrative?.posture?.continuity_score ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeNarrative}>
                Observe drift (NCC-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {narrativeCandidates.map((c) => (
                  <article key={c.candidate_id || c.beat_id} className="workflow-card page-panel">
                    <strong>{c.beat_kind} · {c.candidate_id || c.beat_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <div className="workflow-step-type">ncc={c.ncc_class} · identity={String(c.identity_alignment)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptNarrativeBeat(c)}>
                      Adopt (NCC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'autobiographical' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted: {autobiographical?.posture?.adopted_episodes ?? '—'} · candidates:{' '}
                {autobiographical?.posture?.candidate_episodes ?? '—'} · ongoing work:{' '}
                {autobiographical?.posture?.ongoing_work_count ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeAutobiographical}>
                Observe drift (AAC-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {autobiographicalCandidates.map((c) => (
                  <article key={c.candidate_id || c.episode_id} className="workflow-card page-panel">
                    <strong>{c.episode_kind} · {c.candidate_id || c.episode_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <div className="workflow-step-type">aac={c.aac_class} · identity={String(c.identity_alignment)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptAutobiographicalEpisode(c)}>
                      Adopt (AAC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'social' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted: {social?.posture?.adopted_bonds ?? '—'} · candidates:{' '}
                {social?.posture?.candidate_bonds ?? '—'} · federated peers:{' '}
                {social?.posture?.federated_peer_count ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeSocial}>
                Observe drift (SCC-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {socialCandidates.map((c) => (
                  <article key={c.candidate_id || c.bond_id} className="workflow-card page-panel">
                    <strong>{c.bond_kind} · {c.candidate_id || c.bond_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <div className="workflow-step-type">scc={c.scc_class} · trust={c.trust_posture}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptSocialBond(c)}>
                      Adopt (SCC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'multi-being' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted: {multiBeing?.posture?.adopted_pacts ?? '—'} · candidates:{' '}
                {multiBeing?.posture?.candidate_pacts ?? '—'} · cross-organism peers:{' '}
                {multiBeing?.posture?.cross_organism_peer_count ?? '—'} · digest verified:{' '}
                {multiBeing?.posture?.digest_verified_count ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeMultiBeing}>
                Observe drift (MBC-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {multiBeingCandidates.map((c) => (
                  <article key={c.candidate_id || c.pact_id} className="workflow-card page-panel">
                    <strong>
                      {c.pact_kind} · {c.candidate_id || c.pact_id}
                      {c.digest_verified ? ' · digest-verified' : ''}
                    </strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <div className="workflow-step-type">mbc={c.mbc_class} · trust={c.trust_tier}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptMultiBeingPact(c)}>
                      Adopt (MBC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'culture-of-beings' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted norms: {cultureOfBeings?.posture?.adopted_norms ?? '—'} · candidates:{' '}
                {cultureOfBeings?.posture?.candidate_norms ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeCultureOfBeings}>
                Observe drift (COB-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {cultureOfBeingsCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.norm_kind} · {c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptSharedNorm(c)}>
                      Adopt (COB-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'ecosystems' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted charters: {ecosystems?.posture?.adopted_charters ?? '—'} · candidates:{' '}
                {ecosystems?.posture?.candidate_charters ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeEcosystems}>
                Observe drift (CEC-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {ecosystemCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.charter_kind} · {c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptCharter(c)}>
                      Adopt (CEC-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'membrane' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted policies: {governanceMembrane?.posture?.adopted_policies ?? '—'} · channels:{' '}
                {governanceMembrane?.posture?.permeability_channels ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeMembrane}>
                Observe drift (MGM-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {membraneCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.policy_kind} · {c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptMembranePolicy(c)}>
                      Adopt (MGM-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'diplomacy' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted accords: {diplomacy?.posture?.adopted_accords ?? '—'} · candidates:{' '}
                {diplomacy?.posture?.candidate_accords ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeDiplomacy}>
                Observe drift (ISD-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {diplomacyCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.accord_kind} · {c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptDiplomaticAccord(c)}>
                      Adopt (ISD-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'norm-federations' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted treaties: {normFederations?.posture?.adopted_treaties ?? '—'} · candidates:{' '}
                {normFederations?.posture?.candidate_treaties ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeNormFederations}>
                Observe drift (NFD-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {normFederationCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.treaty_kind} · {c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptNormFederationTreaty(c)}>
                      Adopt (NFD-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'constitutional-evolution' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted amendments: {constitutionalEvolution?.posture?.adopted_amendments ?? '—'} · candidates:{' '}
                {constitutionalEvolution?.posture?.candidate_amendments ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeConstitutionalEvolution}>
                Observe drift (CEV-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {amendmentCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.amendment_kind} · {c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptCharterAmendment(c)}>
                      Adopt (CEV-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'civilizations' ? (
            <div className="workflow-card page-panel">
              <p>
                Adopted civilizations: {civilizations?.posture?.adopted_civilizations ?? '—'} · candidates:{' '}
                {civilizations?.posture?.candidate_civilizations ?? '—'}
              </p>
              <button type="button" className="workflow-secondary-btn" onClick={observeCivilizations}>
                Observe drift (GCV-0)
              </button>
              <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
                {civilizationCandidates.map((c) => (
                  <article key={c.candidate_id} className="workflow-card page-panel">
                    <strong>{c.candidate_id}</strong>
                    <div className="workflow-step-type">{c.summary?.slice(0, 120)}</div>
                    <button type="button" className="workflow-secondary-btn" onClick={() => adoptCivilizationCharter(c)}>
                      Adopt (GCV-2)
                    </button>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {tab === 'chain' ? (
            <div className="workflow-card page-panel">
              <label>
                Workflow id
                <input value={chainId} onChange={(e) => setChainId(e.target.value)} style={{ marginLeft: '0.5rem' }} />
              </label>
              <button type="button" className="workflow-secondary-btn" onClick={runChain} style={{ marginLeft: '0.5rem' }}>
                Run chain (dry-run)
              </button>
            </div>
          ) : null}
          {plugins?.plugs?.length ? (
            <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
              <strong>Plug registry ({plugins.plug_count} · {plugins.enabled_count} enabled)</strong>
              {plugins.plugs.slice(0, 20).map((plug) => (
                <article key={plug.plug_id} className="workflow-card page-panel">
                  <div className="workflow-approval-header">
                    <div>
                      <strong>{plug.plug_id}</strong>
                      <div className="workflow-step-type">{plug.plug_class} · {plug.authority_level}</div>
                    </div>
                    <button
                      type="button"
                      className="workflow-secondary-btn"
                      onClick={() => togglePlug(plug.plug_id, !plug.enabled)}
                    >
                      {plug.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export default OperatorPlugins;
