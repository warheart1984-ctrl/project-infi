import React, { useState } from 'react';
import toast from 'react-hot-toast';
import './Settings.css';

function Settings() {
  const [settings, setSettings] = useState({
    theme: 'dark',
    notifications: true,
    autoSave: true,
    apiUrl: 'http://localhost:5000',
    defaultModel: 'mistralai/Mistral-7B-Instruct-v0.1',
    defaultTemperature: 0.7,
    defaultMaxLength: 512
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    setSaved(false);
  };

  const handleSave = () => {
    localStorage.setItem('aais-settings', JSON.stringify(settings));
    setSaved(true);
    toast.success('Settings saved successfully!');
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    if (window.confirm('Reset all settings to default?')) {
      const defaultSettings = {
        theme: 'dark',
        notifications: true,
        autoSave: true,
        apiUrl: 'http://localhost:5000',
        defaultModel: 'mistralai/Mistral-7B-Instruct-v0.1',
        defaultTemperature: 0.7,
        defaultMaxLength: 512
      };
      setSettings(defaultSettings);
      localStorage.removeItem('aais-settings');
      toast.success('Settings reset to default');
    }
  };

  return (
    <div className="settings">
      <h1>Settings</h1>
      
      <div className="settings-container">
        <div className="settings-section">
          <h2>Appearance</h2>
          <div className="setting-item">
            <label>Theme</label>
            <select
              value={settings.theme}
              onChange={(e) => handleChange('theme', e.target.value)}
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto</option>
            </select>
          </div>
        </div>

        <div className="settings-section">
          <h2>Notifications</h2>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => handleChange('notifications', e.target.checked)}
              />
              Enable Notifications
            </label>
          </div>
        </div>

        <div className="settings-section">
          <h2>Auto-Save</h2>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.autoSave}
                onChange={(e) => handleChange('autoSave', e.target.checked)}
              />
              Auto-save generated content
            </label>
          </div>
        </div>

        <div className="settings-section">
          <h2>API Configuration</h2>
          <div className="setting-item">
            <label>API URL</label>
            <input
              type="text"
              value={settings.apiUrl}
              onChange={(e) => handleChange('apiUrl', e.target.value)}
              placeholder="http://localhost:5000"
            />
          </div>
        </div>

        <div className="settings-section">
          <h2>Default Model Settings</h2>
          <div className="setting-item">
            <label>Default Model</label>
            <select
              value={settings.defaultModel}
              onChange={(e) => handleChange('defaultModel', e.target.value)}
            >
              <option value="mistralai/Mistral-7B-Instruct-v0.1">Mistral-7B</option>
              <option value="meta-llama/Llama-2-7b-chat-hf">Llama-2-7B</option>
              <option value="gpt2">GPT-2</option>
            </select>
          </div>

          <div className="setting-item">
            <label>Default Temperature: {settings.defaultTemperature.toFixed(2)}</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.defaultTemperature}
              onChange={(e) => handleChange('defaultTemperature', Number(e.target.value))}
            />
          </div>

          <div className="setting-item">
            <label>Default Max Length: {settings.defaultMaxLength}</label>
            <input
              type="range"
              min="100"
              max="2000"
              step="100"
              value={settings.defaultMaxLength}
              onChange={(e) => handleChange('defaultMaxLength', Number(e.target.value))}
            />
          </div>
        </div>

        <div className="settings-section">
          <h2>About</h2>
          <div className="about-info">
            <p><strong>AAIS Version:</strong> 0.1.0</p>
            <p><strong>Frontend:</strong> React 18.2</p>
            <p><strong>Backend:</strong> Python Flask</p>
            <p><strong>Status:</strong> ✅ Connected</p>
          </div>
        </div>

        <div className="settings-actions">
          <button className="save-btn" onClick={handleSave}>
            {saved ? '✓ Saved' : 'Save Settings'}
          </button>
          <button className="reset-btn" onClick={handleReset}>
            Reset to Default
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;
