export function validateProposedEdge({ nodes = [], edges = [], connection = {} }) {
  const source = connection.source;
  const target = connection.target;
  if (!source || !target) {
    throw new Error('Workflow edges need a source and target.');
  }
  if (source === target) {
    throw new Error('Workflow edges cannot point to the same node.');
  }
  const ids = new Set(nodes.map((node) => node.id));
  if (!ids.has(source) || !ids.has(target)) {
    throw new Error('Workflow edge references an unknown node.');
  }
  if (edges.some((edge) => edge.source === source && edge.target === target)) {
    throw new Error('Workflow edge already exists.');
  }
  return true;
}

export function validateAndBuildWorkflowPayload({ workflowName, nodes = [], edges = [], cisivStage }) {
  const name = String(workflowName || '').trim();
  if (!name) {
    throw new Error('Workflow name is required.');
  }
  if (!Array.isArray(nodes) || nodes.length === 0) {
    throw new Error('Add at least one workflow node.');
  }
  return {
    name,
    nodes,
    edges,
    cisiv_stage: cisivStage || 'structure',
  };
}
