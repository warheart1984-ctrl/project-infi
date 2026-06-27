const TARGETS = [
  { path: '/', label: 'Small Nova', expectedText: 'Small Nova' },
  { path: '/jarvis', label: 'Jarvis Console', expectedText: 'Jarvis' },
  { path: '/operator', label: 'Operator Console', expectedText: 'Operator' },
];

export function listBrowserVerificationTargets() {
  return TARGETS;
}

export function getBrowserExpectationGuide(path = '/') {
  return TARGETS.find((target) => target.path === path) || {
    path,
    label: path,
    expectedText: '',
  };
}
