const vscode = acquireVsCodeApi();

let messages = [];
let config = {
  governanceMode: true,
  preferredBackend: 'auto',
  availableBackends: [],
  skippedBackends: [],
};

const app = document.getElementById('app');

function render() {
  if (messages.length === 0) {
    app.innerHTML = `
      <div class="empty-state">
        <h2>AAIS Coding Assistant</h2>
        <p>Governance-first coding with local & cloud backends</p>
        <p style="margin-top: 12px; font-size: 12px;">
          Press <kbd>Ctrl+Alt+A</kbd> (Win/Linux) or <kbd>Cmd+Alt+A</kbd> (Mac) to open
        </p>
        <div style="margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;">
          <span class="status-badge">${config.governanceMode ? 'Governance ON' : 'Governance OFF'}</span>
          <span class="status-badge">${config.preferredBackend}</span>
        </div>
      </div>
      ${renderInputArea()}
    `;
  } else {
    app.innerHTML = `
      <div class="header">
        <h1>AAIS Chat</h1>
        <span class="status-badge">${config.governanceMode ? 'Governance ON' : 'Governance OFF'}</span>
        <span class="status-badge">${config.preferredBackend}</span>
      </div>
      <div class="messages" id="messages">
        ${messages.map(renderMessage).join('')}
      </div>
      ${renderInputArea()}
    `;
    scrollToBottom();
  }
  bindEvents();
}

function renderMessage(msg) {
  const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const streaming = msg.streaming ? '<span class="streaming-indicator"></span>' : '';
  const backend = msg.backend ? `<span class="backend-tag">${msg.backend}</span>` : '';
  const errorClass = msg.error ? ' error' : '';
  
  return `
    <div class="message ${msg.role}${errorClass}">
      <div class="message-header">
        <span class="role-badge">${msg.role}</span>
        <span>${time}</span>
        ${backend}
        ${streaming}
      </div>
      <div class="message-content">${escapeHtml(msg.content)}</div>
    </div>
  `;
}

function renderInputArea() {
  const backends = ['auto', ...config.availableBackends];
  const backendOptions = backends.map(b => `<option value="${b}" ${b === config.preferredBackend ? 'selected' : ''}>${b}</option>`).join('');
  
  return `
    <div class="input-area">
      <div class="controls">
        <label><input type="checkbox" id="governanceToggle" ${config.governanceMode ? 'checked' : ''}> Governance</label>
        <select id="backendSelect">${backendOptions}</select>
        <button class="clear-btn" id="clearBtn">Clear</button>
      </div>
      <div class="input-row">
        <textarea id="input" placeholder="Ask AAIS anything... (Shift+Enter for new line)" rows="1"></textarea>
        <button id="sendBtn" disabled>Send</button>
      </div>
    </div>
  `;
}

function bindEvents() {
  const input = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');
  const clearBtn = document.getElementById('clearBtn');
  const governanceToggle = document.getElementById('governanceToggle');
  const backendSelect = document.getElementById('backendSelect');

  if (input) {
    input.addEventListener('input', () => {
      sendBtn.disabled = !input.value.trim();
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 160) + 'px';
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (input.value.trim()) sendMessage();
      }
    });
    input.focus();
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      vscode.postMessage({ type: 'clear' });
    });
  }

  if (governanceToggle) {
    governanceToggle.addEventListener('change', (e) => {
      vscode.postMessage({ type: 'toggleGovernance' });
    });
  }

  if (backendSelect) {
    backendSelect.addEventListener('change', (e) => {
      vscode.postMessage({ type: 'setBackend', backend: e.target.value });
    });
  }
}

function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = 'auto';
  vscode.postMessage({ type: 'send', text });
}

function scrollToBottom() {
  const messagesEl = document.getElementById('messages');
  if (messagesEl) {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

window.addEventListener('message', event => {
  const message = event.data;
  switch (message.type) {
    case 'messages':
      messages = message.messages;
      config = message.config;
      render();
      break;
    case 'refresh':
      config = message.config;
      render();
      break;
  }
});

// Initial render
render();