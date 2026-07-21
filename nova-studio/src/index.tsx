import { createRoot } from 'react-dom/client';

import { StudioApp } from './components/StudioApp';

const container = document.getElementById('root');

if (container) {
  createRoot(container).render(<StudioApp />);
}
