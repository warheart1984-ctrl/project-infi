import React, { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  Position,
  Handle,
  addEdge,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import ReactFlow from 'reactflow';
import { FiExternalLink, FiPlay, FiPlus, FiSave, FiTrash2, FiZap } from 'react-icons/fi';
import { Link, UNSAFE_NavigationContext as NavigationContext, useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, apiPut, getApiErrorMessage } from '../lib/api';
import { buildSeedWorkflowFromOnboarding } from '../lib/workflowOnboarding';
import { validateAndBuildWorkflowPayload, validateProposedEdge } from '../lib/workflowValidation';
import './WorkflowBuilder.css';
import 'reactflow/dist/style.css';

const TRIGGER_TYPES = ['email.received', 'slack.message', 'webhook.received', 'schedule.tick'];
const ACTION_TYPES = ['ai.analyze', 'slack.send', 'email.send', 'api.call', 'task.create'];
const CONDITION_TYPES = ['contains_text', 'high_priority', 'from_domain', 'confidence_above'];

const initialNodes = [
  {
    id: 'trigger-1',
    type: 'triggerNode',
    position: { x: 60, y: 200 },
    data: {
      label: 'Incoming Email',
      kind: 'trigger',
      subtype: 'email.received',
      config: { inbox: 'primary' },
    },
  },
  {
    id: 'action-1',
    type: 'actionNode',
    position: { x: 390, y: 150 },
    data: {
      label: 'Summarize with AI',
      kind: 'action',
      subtype: 'ai.analyze',
      config: { goal: 'Summarize email and detect urgency' },
    },
  },
  {
    id: 'action-2',
    type: 'actionNode',
    position: { x: 730, y: 150 },
    data: {
      label: 'Send to Slack',
      kind: 'action',
      subtype: 'slack.send',
      config: { channel: '#alerts' },
    },
  },
];

const initialEdges = [
  {
    id: 'e1',
    source: 'trigger-1',
    target: 'action-1',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e2',
    source: 'action-1',
    target: 'action-2',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
];

function TriggerNode({ data, selected }) {
  return (
    <div className={`workflow-node workflow-node-trigger ${selected ? 'selected' : ''}`}>
      <div className="workflow-node-title">Trigger</div>
      <div className="workflow-node-label">{data.label}</div>
      <div className="workflow-node-chip">{data.subtype}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

function ConditionNode({ data, selected }) {
  return (
    <div className={`workflow-node workflow-node-condition ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="workflow-node-title">Condition</div>
      <div className="workflow-node-label">{data.label}</div>
      <div className="workflow-node-chip">{data.subtype}</div>
      <Handle type="source" id="true" position={Position.Right} style={{ top: '38%' }} />
      <Handle type="source" id="false" position={Position.Right} style={{ top: '70%' }} />
    </div>
  );
}

function ActionNode({ data, selected }) {
  return (
    <div className={`workflow-node workflow-node-action ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="workflow-node-title">Action</div>
      <div className="workflow-node-label">{data.label}</div>
      <div className="workflow-node-chip">{data.subtype}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = {
  triggerNode: TriggerNode,
  conditionNode: ConditionNode,
  actionNode: ActionNode,
};

function getWorkflowSignature(name, nodes, edges) {
  return JSON.stringify({
    name,
    nodes,
    edges,
  });
}

function useUnsavedWorkflowPrompt(when, message) {
  const { navigator } = useContext(NavigationContext);

  useEffect(() => {
    if (!when || !navigator?.block) {
      return undefined;
    }

    const unblock = navigator.block((tx) => {
      const shouldLeave = window.confirm(message);
      if (!shouldLeave) {
        return;
      }
      unblock();
      tx.retry();
    });

    return unblock;
  }, [message, navigator, when]);
}

function defaultNodeData(kind) {
  if (kind === 'trigger') {
    return {
      label: 'New Trigger',
      kind,
      subtype: TRIGGER_TYPES[0],
      config: { source: 'default' },
    };
  }
  if (kind === 'condition') {
    return {
      label: 'New Condition',
      kind,
      subtype: CONDITION_TYPES[0],
      config: { value: '' },
    };
  }
  return {
    label: 'New Action',
    kind,
    subtype: ACTION_TYPES[0],
    config: { target: '' },
  };
}

function nodeTypeForKind(kind) {
  if (kind === 'trigger') return 'triggerNode';
  if (kind === 'condition') return 'conditionNode';
  return 'actionNode';
}

function WorkflowBuilder() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryWorkflowId = searchParams.get('workflowId');
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState(initialNodes[0].id);
  const [workflowName, setWorkflowName] = useState('Email Summary to Slack');
  const [aiPrompt, setAiPrompt] = useState('When I get an important email, summarize it and send it to Slack.');
  const [jsonPreview, setJsonPreview] = useState('');
  const [workflowId, setWorkflowId] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState('Ready.');
  const [onboardingState, setOnboardingState] = useState(null);
  const [lastSavedSignature, setLastSavedSignature] = useState(
    getWorkflowSignature('Email Summary to Slack', initialNodes, initialEdges),
  );
  const [hasAppliedOnboardingSeed, setHasAppliedOnboardingSeed] = useState(false);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) || null,
    [nodes, selectedNodeId],
  );
  const currentSignature = useMemo(
    () => getWorkflowSignature(workflowName, nodes, edges),
    [edges, nodes, workflowName],
  );
  const hasUnsavedChanges = currentSignature !== lastSavedSignature;
  useUnsavedWorkflowPrompt(hasUnsavedChanges, 'You have unsaved workflow changes. Leave this page anyway?');

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      if (!hasUnsavedChanges) {
        return;
      }
      event.preventDefault();
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasUnsavedChanges]);

  useEffect(() => {
    let active = true;

    const loadOnboarding = async () => {
      try {
        const response = await apiGet('/onboarding');
        if (active) {
          setOnboardingState(response.data);
        }
      } catch {
        // Ignore onboarding fetch failures and keep the builder usable.
      }
    };

    loadOnboarding();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadWorkflow() {
      try {
        setIsLoading(true);
        const path = queryWorkflowId
          ? `/workflows?workflow_id=${encodeURIComponent(queryWorkflowId)}`
          : '/workflows?latest=true';
        const response = await apiGet(path);
        const workflow = response.data.workflow;

        if (cancelled || !workflow) {
          if (!cancelled) {
            setStatusMessage(queryWorkflowId ? 'Workflow not found. Starting with a draft.' : 'Starting with a draft.');
          }
          return;
        }

        setWorkflowId(workflow.id);
        setWorkflowName(workflow.name || 'Untitled Workflow');
        if (Array.isArray(workflow.nodes) && workflow.nodes.length > 0) {
          setNodes(workflow.nodes);
          setSelectedNodeId(workflow.nodes[0].id);
        }
        if (Array.isArray(workflow.edges)) {
          setEdges(workflow.edges);
        }
        setJsonPreview(JSON.stringify(workflow.config || {}, null, 2));
        setLastSavedSignature(
          getWorkflowSignature(
            workflow.name || 'Untitled Workflow',
            Array.isArray(workflow.nodes) ? workflow.nodes : initialNodes,
            Array.isArray(workflow.edges) ? workflow.edges : initialEdges,
          ),
        );
        setStatusMessage(`Loaded workflow: ${workflow.name}`);
      } catch {
        if (!cancelled) {
          setStatusMessage('Starting with a draft.');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadWorkflow();
    return () => {
      cancelled = true;
    };
  }, [queryWorkflowId, setEdges, setNodes]);

  useEffect(() => {
    if (
      isLoading ||
      workflowId ||
      queryWorkflowId ||
      hasAppliedOnboardingSeed ||
      !onboardingState?.onboarding_done
    ) {
      return;
    }

    const seededDraft = buildSeedWorkflowFromOnboarding(onboardingState);
    if (!seededDraft) {
      return;
    }

    setWorkflowName(seededDraft.workflowName);
    setAiPrompt(seededDraft.aiPrompt);
    setNodes(seededDraft.nodes);
    setEdges(seededDraft.edges);
    setSelectedNodeId(seededDraft.nodes[0]?.id || null);
    setLastSavedSignature(
      getWorkflowSignature(seededDraft.workflowName, seededDraft.nodes, seededDraft.edges),
    );
    setJsonPreview('');
    setStatusMessage('Seeded a builder draft from your onboarding preferences.');
    setHasAppliedOnboardingSeed(true);
  }, [
    hasAppliedOnboardingSeed,
    isLoading,
    onboardingState,
    queryWorkflowId,
    setEdges,
    setNodes,
    workflowId,
  ]);

  const onConnect = useCallback(
    (params) => {
      try {
        validateProposedEdge({ nodes, edges, connection: params });
        setEdges((current) =>
          addEdge(
            {
              ...params,
              markerEnd: { type: MarkerType.ArrowClosed },
            },
            current,
          ),
        );
      } catch (error) {
        const message = getApiErrorMessage(error, 'That connection is not valid.');
        setStatusMessage(message);
        toast.error(message);
      }
    },
    [edges, nodes, setEdges],
  );

  const addNode = (kind) => {
    const id = `${kind}-${crypto.randomUUID().slice(0, 8)}`;
    const count = nodes.filter((node) => node.data.kind === kind).length;
    const nextNode = {
      id,
      type: nodeTypeForKind(kind),
      position: { x: 160 + count * 110, y: 80 + count * 100 },
      data: defaultNodeData(kind),
    };

    setNodes((current) => [...current, nextNode]);
    setSelectedNodeId(id);
  };

  const updateSelectedNode = (patch) => {
    if (!selectedNode) return;
    setNodes((current) =>
      current.map((node) =>
        node.id === selectedNode.id
          ? {
              ...node,
              data: {
                ...node.data,
                ...patch,
              },
            }
          : node,
      ),
    );
  };

  const updateSelectedNodeConfig = (key, value) => {
    if (!selectedNode) return;
    setNodes((current) =>
      current.map((node) =>
        node.id === selectedNode.id
          ? {
              ...node,
              data: {
                ...node.data,
                config: {
                  ...node.data.config,
                  [key]: value,
                },
              },
            }
          : node,
      ),
    );
  };

  const removeSelectedNode = () => {
    if (!selectedNode) return;
    setEdges((current) => current.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id));
    setNodes((current) => current.filter((node) => node.id !== selectedNode.id));
    setSelectedNodeId(null);
  };

  const buildWorkflowPayload = useCallback(() => {
    return validateAndBuildWorkflowPayload({
      workflowName,
      nodes,
      edges,
    });
  }, [edges, nodes, workflowName]);

  const buildWorkflowJson = useCallback(() => {
    const payload = buildWorkflowPayload();
    setJsonPreview(JSON.stringify(payload, null, 2));
    return payload;
  }, [buildWorkflowPayload]);

  const saveWorkflow = async () => {
    try {
      setIsSaving(true);
      setStatusMessage('Saving workflow...');
      const config = buildWorkflowJson();
      const response = workflowId
        ? await apiPut('/workflows', {
            id: workflowId,
            name: workflowName,
            nodes,
            edges,
            config,
          })
        : await apiPost('/workflows', {
            name: workflowName,
            nodes,
            edges,
            config,
          });
      const saved = response.data.workflow;
      if (saved?.id) {
        setWorkflowId(saved.id);
        if (Array.isArray(saved.nodes)) {
          setNodes(saved.nodes);
        }
        if (Array.isArray(saved.edges)) {
          setEdges(saved.edges);
        }
        if (saved.config) {
          setJsonPreview(JSON.stringify(saved.config, null, 2));
        }
        setLastSavedSignature(
          getWorkflowSignature(
            saved.name || workflowName,
            Array.isArray(saved.nodes) ? saved.nodes : nodes,
            Array.isArray(saved.edges) ? saved.edges : edges,
          ),
        );
        navigate(`/workflows?workflowId=${saved.id}`, { replace: true });
      }
      setStatusMessage('Workflow saved.');
      toast.success('Workflow saved');
    } catch (error) {
      const message = getApiErrorMessage(error, 'Could not save workflow');
      setStatusMessage(message);
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  const runWorkflowNow = async () => {
    try {
      setIsSimulating(true);
      setStatusMessage('Queueing workflow run...');

      if (!workflowId) {
        setStatusMessage('Save the workflow first before running it live.');
        toast.error('Save the workflow first before running it live.');
        return;
      }

      const response = await apiPost('/workflows/run', {
        id: workflowId,
        trigger_data: {
          text: 'Manual run from workflow builder',
          source: 'builder',
        },
      });

      const runId = response.data.workflow_run_id;
      setStatusMessage('Workflow queued.');
      toast.success('Workflow queued');

      if (runId) {
        navigate(`/workflows/runs/${runId}`);
      }
    } catch (error) {
      const message = getApiErrorMessage(error, 'Workflow queue failed');
      setStatusMessage(message);
      toast.error(message);
    } finally {
      setIsSimulating(false);
    }
  };

  const simulateRun = async () => {
    try {
      setIsSimulating(true);
      setStatusMessage('Simulating workflow...');
      const payload = buildWorkflowJson();
      const response = await apiPost('/workflows/simulate', {
        id: workflowId,
        workflow: payload,
      });
      setJsonPreview(JSON.stringify(response.data, null, 2));
      setStatusMessage('Simulation complete.');
    } catch (error) {
      const message = getApiErrorMessage(error, 'Simulation failed');
      setStatusMessage(message);
      toast.error(message);
    } finally {
      setIsSimulating(false);
    }
  };

  const generateFromPrompt = async () => {
    try {
      setIsGenerating(true);
      setStatusMessage('Generating workflow with AI...');
      const response = await apiPost('/workflows/generate', {
        prompt: aiPrompt,
        name: workflowName,
      });
      const workflow = response.data.workflow;
      if (workflow?.name) {
        setWorkflowName(workflow.name);
      }
      if (Array.isArray(workflow?.nodes) && workflow.nodes.length > 0) {
        setNodes(workflow.nodes);
        setSelectedNodeId(workflow.nodes[0].id);
      }
      if (Array.isArray(workflow?.edges)) {
        setEdges(workflow.edges);
      }
      setJsonPreview(JSON.stringify(workflow?.config || workflow, null, 2));
      setStatusMessage('Workflow generated.');
    } catch (error) {
      const message = getApiErrorMessage(error, 'Generation failed');
      setStatusMessage(message);
      toast.error(message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="workflow-builder-page">
      <div className="page-intro">
        <h1>Workflow Builder</h1>
        <p>
          Design trigger-to-action automations, queue live runs, and inspect execution without leaving the main AAIS
          console.
        </p>
      </div>

      <section className="workflow-builder-banner page-panel">
        <div>
          <span className="status-pill connected">{isLoading ? 'Loading' : 'Workflow studio ready'}</span>
          <p className="workflow-builder-banner-copy">{statusMessage}</p>
        </div>

        <div className="workflow-builder-banner-links">
          <Link to="/workflows/runs">
            Run history <FiExternalLink />
          </Link>
          <Link to="/workflows/approvals">
            Approvals <FiExternalLink />
          </Link>
          <Link to="/workflows/templates">
            Templates <FiExternalLink />
          </Link>
        </div>
      </section>

      {!onboardingState?.onboarding_done ? (
        <section className="workflow-builder-onboarding page-panel">
          <div>
            <h2>Start from a guided setup</h2>
            <p>Tell AAIS what you want to automate, then jump straight into templates instead of a blank canvas.</p>
          </div>
          <Link className="workflow-cta-link" to="/onboarding">
            Open onboarding
          </Link>
        </section>
      ) : null}

      {onboardingState?.onboarding_done && !workflowId ? (
        <section className="workflow-builder-onboarding page-panel">
          <div>
            <h2>Builder seeded from onboarding</h2>
            <p>
              This draft reflects your saved goal and preferred tools. Save it when you want to create a reusable
              workflow.
            </p>
          </div>
          <Link className="workflow-cta-link" to="/workflows/templates">
            Compare templates
          </Link>
        </section>
      ) : null}

      <div className="workflow-builder-layout">
        <section className="workflow-sidebar page-panel">
          <div className="workflow-section">
            <label className="workflow-label">Workflow Name</label>
            <input value={workflowName} onChange={(event) => setWorkflowName(event.target.value)} type="text" />
          </div>

          <div className="workflow-section">
            <label className="workflow-label">Generate With AI</label>
            <textarea
              value={aiPrompt}
              onChange={(event) => setAiPrompt(event.target.value)}
              placeholder="When I get an email, summarize it and send it to Slack..."
            />
            <button className="workflow-primary-btn" onClick={generateFromPrompt} disabled={isGenerating}>
              <FiZap /> Generate Draft
            </button>
          </div>

          <div className="workflow-section">
            <div className="workflow-label">Add Nodes</div>
            <div className="workflow-action-grid">
              <button className="workflow-secondary-btn" onClick={() => addNode('trigger')}>
                <FiPlus /> Trigger
              </button>
              <button className="workflow-secondary-btn" onClick={() => addNode('condition')}>
                <FiPlus /> Condition
              </button>
              <button className="workflow-secondary-btn" onClick={() => addNode('action')}>
                <FiPlus /> Action
              </button>
            </div>
          </div>

          <div className="workflow-section">
            <div className="workflow-label">Run Controls</div>
            <div className="workflow-run-grid">
              <button className="workflow-primary-btn" onClick={simulateRun} disabled={isSimulating || isLoading}>
                <FiPlay /> Simulate
              </button>
              <button className="workflow-primary-btn workflow-live-btn" onClick={runWorkflowNow} disabled={isSimulating || isLoading}>
                <FiPlay /> Run Live
              </button>
              <button className="workflow-secondary-btn" onClick={saveWorkflow} disabled={isSaving || isLoading}>
                <FiSave /> Save
              </button>
            </div>
          </div>

          <div className="workflow-section workflow-preview-panel">
            <div className="workflow-label">JSON Preview</div>
            {jsonPreview ? (
              <pre>{jsonPreview}</pre>
            ) : (
              <div className="workflow-empty-state">Build or simulate the workflow to preview the payload.</div>
            )}
          </div>
        </section>

        <section className="workflow-canvas page-panel">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            fitView
          >
            <MiniMap pannable zoomable />
            <Controls />
            <Background gap={24} color="rgba(92, 231, 255, 0.08)" />
          </ReactFlow>
        </section>

        <aside className="workflow-inspector page-panel">
          <div className="workflow-inspector-header">
            <div>
              <div className="workflow-label">Node Inspector</div>
              <p>Adjust labels, action types, and config without leaving the canvas.</p>
            </div>
            <button className="workflow-icon-btn" onClick={removeSelectedNode} disabled={!selectedNode}>
              <FiTrash2 />
            </button>
          </div>

          {selectedNode ? (
            <div className="workflow-inspector-fields">
              <div className="workflow-section">
                <label className="workflow-label">Label</label>
                <input
                  type="text"
                  value={selectedNode.data.label}
                  onChange={(event) => updateSelectedNode({ label: event.target.value })}
                />
              </div>

              <div className="workflow-section">
                <label className="workflow-label">Subtype</label>
                <select
                  value={selectedNode.data.subtype}
                  onChange={(event) => updateSelectedNode({ subtype: event.target.value })}
                >
                  {(selectedNode.data.kind === 'trigger'
                    ? TRIGGER_TYPES
                    : selectedNode.data.kind === 'condition'
                    ? CONDITION_TYPES
                    : ACTION_TYPES
                  ).map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              <div className="workflow-section">
                <div className="workflow-label">Config</div>
                {Object.entries(selectedNode.data.config).map(([key, value]) => (
                  <div className="workflow-config-row" key={key}>
                    <label>{key}</label>
                    <input
                      type="text"
                      value={value}
                      onChange={(event) => updateSelectedNodeConfig(key, event.target.value)}
                    />
                  </div>
                ))}
              </div>

              <div className="workflow-section workflow-hint-panel">
                <div className="workflow-label">Execution Hint</div>
                <p>
                  {selectedNode.data.kind === 'trigger' && 'Starts the workflow when an external event arrives.'}
                  {selectedNode.data.kind === 'condition' &&
                    'Evaluates the incoming data and lets the workflow decide whether to continue.'}
                  {selectedNode.data.kind === 'action' &&
                    'Runs the AI step, integration, or task side-effect for this part of the workflow.'}
                </p>
              </div>
            </div>
          ) : (
            <div className="workflow-empty-state">Select a node to edit its configuration.</div>
          )}
        </aside>
      </div>
    </div>
  );
}

export default WorkflowBuilder;
