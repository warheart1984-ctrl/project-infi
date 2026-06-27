export type StudioMode = 'coding-agent' | 'drift' | 'control' | 'replay';

export type StudioRoute = {
  path: string;
  mode: StudioMode;
  label: string;
};

export const studioRoutes: StudioRoute[] = [
  { path: '/nova/studio', mode: 'coding-agent', label: 'Coding Agent' },
  { path: '/nova/studio/coding-agent', mode: 'coding-agent', label: 'Coding Agent' },
  { path: '/nova/studio/drift', mode: 'drift', label: 'Drift Visualizer' },
  { path: '/nova/studio/control', mode: 'control', label: 'Control Tower' },
  { path: '/nova/studio/replay', mode: 'replay', label: 'Replay & Receipts' },
];

export function getStudioRouteForMode(mode: StudioMode): StudioRoute | undefined {
  return studioRoutes.find((route) => route.mode === mode && route.path !== '/nova/studio')
    ?? studioRoutes.find((route) => route.mode === mode);
}

export function getStudioModeFromPath(path: string): StudioMode {
  const normalized = path.replace(/^#/, '').replace(/\/$/, '');
  return studioRoutes.find((route) => route.path === normalized)?.mode ?? 'coding-agent';
}
