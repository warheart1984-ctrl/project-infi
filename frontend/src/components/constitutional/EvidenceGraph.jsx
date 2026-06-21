import React, { useMemo } from 'react';

const TYPE_COLORS = {
  law: '#f5c542',
  law_ledger: '#b8860b',
  cit: '#6cb6ff',
  mit: '#c792ea',
  eit: '#3dd68c',
  evidence: '#4fd1c5',
  evidence_ref: '#4fd1c5',
  derivation: '#3dd68c',
  observation: '#6cb6ff',
  import: '#c792ea',
  lineage: '#8fa0bf',
  trace: '#8fa0bf',
  dependency: '#ff6b6b',
  ledger_entry: '#4fd1c5',
};

function confidenceBandStroke(band) {
  if (band === 'high') return '#3dd68c';
  if (band === 'mid') return '#f5a623';
  return '#ff6b6b';
}

export function EvidenceGraph({ nodes = [], edges = [], onNodeClick, height = 320 }) {
  const layout = useMemo(() => {
    const width = 720;
    const cols = Math.max(1, Math.ceil(Math.sqrt(nodes.length || 1)));
    const positioned = nodes.map((node, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      return {
        ...node,
        x: 80 + col * (width / (cols + 1)),
        y: 60 + row * 70,
      };
    });
    const byId = Object.fromEntries(positioned.map((node) => [node.id, node]));
    const lines = edges
      .map((edge) => {
        const from = byId[edge.from];
        const to = byId[edge.to];
        if (!from || !to) return null;
        return { ...edge, x1: from.x, y1: from.y, x2: to.x, y2: to.y };
      })
      .filter(Boolean);
    return { width, positioned, lines };
  }, [nodes, edges]);

  if (!nodes.length) {
    return <div className="evidence-graph constitutional-muted">No lineage nodes.</div>;
  }

  return (
    <svg className="evidence-graph" viewBox={`0 0 ${layout.width} ${height}`} role="img" aria-label="Evidence lineage graph">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#8fa0bf" />
        </marker>
      </defs>
      {layout.lines.map((line) => (
        <line
          key={`${line.from}-${line.to}-${line.kind}`}
          x1={line.x1}
          y1={line.y1}
          x2={line.x2}
          y2={line.y2}
          stroke="#44516d"
          strokeWidth="1.5"
          markerEnd="url(#arrow)"
        />
      ))}
      {layout.positioned.map((node) => (
        <g
          key={node.id}
          className="evidence-graph-node"
          onClick={() => onNodeClick?.(node)}
          role="presentation"
        >
          <circle
            r="16"
            cx={node.x}
            cy={node.y}
            fill={TYPE_COLORS[node.type] || '#54617a'}
            stroke={confidenceBandStroke(node.confidence_band)}
            strokeWidth="2"
          />
          <text className="evidence-graph-tooltip" x={node.x} y={node.y + 28} textAnchor="middle">
            {node.label || node.id}
          </text>
        </g>
      ))}
    </svg>
  );
}
