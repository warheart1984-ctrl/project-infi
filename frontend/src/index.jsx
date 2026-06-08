import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { bootstrapAuth } from './lib/bootstrapAuth';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

bootstrapAuth().then(() => {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
});
