from __future__ import annotations

import json
from pathlib import Path

from nova.omega.drift import DriftVector
from nova.omega.heatmap import OmegaHeatmapPoint


def render_dashboard(
    heatmap_points: list[OmegaHeatmapPoint],
    drift_vectors: dict[str, DriftVector],
    omega_score: float,
    out_path: str = "omega_dashboard.html",
) -> None:
    data = {
        "omega_score": omega_score,
        "heatmap": [
            {
                "evidence": point.evidence,
                "correctness": point.correctness,
                "domain": point.domain,
                "survived": point.survived,
            }
            for point in heatmap_points
        ],
        "drift": {
            mode: {
                "capability_delta": vector.capability_delta,
                "guardrail_delta": vector.guardrail_delta,
                "reflection_delta": vector.reflection_delta,
                "planning_delta": vector.planning_delta,
            }
            for mode, vector in drift_vectors.items()
        },
    }

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Omega Survivability Dashboard</title>
  <style>
    body {{ font-family: sans-serif; margin: 20px; }}
    .heatmap {{ display: grid; grid-template-columns: repeat(11, 20px); gap: 2px; }}
    .cell {{ width: 20px; height: 20px; }}
  </style>
</head>
<body>
  <h1>Omega Survivability Dashboard</h1>
  <p>Ω-score: <strong>{omega_score:.3f}</strong></p>

  <h2>Heatmap (evidence × correctness × domain)</h2>
  <div id="heatmap"></div>

  <h2>Drift vectors (per PIT mode)</h2>
  <pre id="drift"></pre>

  <script>
    const data = {json.dumps(data)};

    const container = document.getElementById('heatmap');
    const domains = [...new Set(data.heatmap.map(p => p.domain))];

    domains.forEach(domain => {{
      const title = document.createElement('h3');
      title.textContent = 'Domain: ' + domain;
      container.appendChild(title);

      const grid = document.createElement('div');
      grid.className = 'heatmap';

      const points = data.heatmap.filter(p => p.domain === domain);
      points.forEach(p => {{
        const cell = document.createElement('div');
        cell.className = 'cell';
        cell.title = `e=${{p.evidence}}, c=${{p.correctness}}, survived=${{p.survived}}`;
        cell.style.backgroundColor = p.survived ? '#4caf50' : '#f44336';
        grid.appendChild(cell);
      }});

      container.appendChild(grid);
    }});

    document.getElementById('drift').textContent = JSON.stringify(data.drift, null, 2);
  </script>
</body>
</html>
"""
    Path(out_path).write_text(html, encoding="utf-8")
