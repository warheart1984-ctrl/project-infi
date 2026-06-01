import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { apiGet } from '../lib/api';
import { defaultSettings, getApiBaseUrlCandidates, getSettings, resetSettings, saveSettings } from '../lib/settings';
import './Settings.css';

function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [connectionStatus, setConnectionStatus] = useState('Checking backend...');

  const [saved, setSaved] = useState(false);
  const fallbackCandidates = getApiBaseUrlCandidates(settings.apiUrl).filter((candidate) => candidate !== settings.apiUrl);

  useEffect(() => {
    setSettings(getSettings());
  }, []);

  useEffect(() => {
    let active = true;

    apiGet('/health')
      .then((response) => {
        if (active) {
          const activeMode = response.data.active_model_mode || 'not_initialized';
          setConnectionStatus(`Connected (${activeMode})`);
        }
      })
      .catch(() => {
        if (active) {
          setConnectionStatus('Backend unavailable');
        }
      });

    return () => {
      active = false;
    };
  }, [settings.apiUrl]);

  const handleChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    setSaved(false);
  };

  const handleSave = () => {
    saveSettings(settings);
    setSaved(true);
    toast.success('Settings saved successfully!');
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    if (window.confirm('Reset all settings to default?')) {
      setSettings(resetSettings());
      toast.success('Settings reset to default');
    }
  };

  return (
    <div className="settings">
      <div className="page-intro">
        <h1>Settings</h1>
        <p>Local configuration for the browser app, including the backend base URL and default generation options.</p>
      </div>
      
      <div className="settings-container page-panel">
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
              placeholder={defaultSettings.apiUrl}
            />
          </div>
          <div className="about-info">
            <p><strong>Selected runtime:</strong> {settings.apiUrl}</p>
            <p><strong>Local fallback order:</strong> {[settings.apiUrl, ...fallbackCandidates].join(' → ')}</p>
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
              <option value="auto">Auto detect</option>
              <option value="mock">Mock local mode</option>
              <option value="real">Real model stack</option>
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
              min="64"
              max="1024"
              step="32"
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
            <p><strong>Backend:</strong> Launcher-selected local runtime</p>
            <p><strong>Status:</strong> {connectionStatus}</p>
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
