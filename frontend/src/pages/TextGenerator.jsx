import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { apiPost, getApiErrorMessage } from '../lib/api';
import { addHistoryEntry } from '../lib/history';
import { getSettings } from '../lib/settings';
import './TextGenerator.css';

function TextGenerator() {
  const [prompt, setPrompt] = useState('');
  const [maxLength, setMaxLength] = useState(256);
  const [temperature, setTemperature] = useState(0.6);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');

  useEffect(() => {
    const settings = getSettings();
    setMaxLength(settings.defaultMaxLength);
    setTemperature(settings.defaultTemperature);
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setLoading(true);
    try {
      const response = await apiPost('/api/text/generate', {
        prompt,
        max_length: maxLength,
        temperature
      });
      setResult(response.data.generated_text);
      addHistoryEntry({
        type: 'text',
        prompt,
        output: response.data.generated_text,
        model: 'AAIS local API',
      });
      toast.success('Text generated successfully!');
    } catch (error) {
      toast.error(`Error generating text: ${getApiErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(result);
    toast.success('Copied to clipboard!');
  };

  return (
    <div className="text-generator">
      <div className="page-intro">
        <h1>Prompt Lab</h1>
        <p>
          Send direct prompts to the local model stack, inspect the raw response,
          and compare it against the Jarvis chat experience.
        </p>
      </div>
      
      <div className="generator-container">
        <div className="input-section page-panel">
          <label>Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
            rows="6"
          />

          <div className="controls">
            <div className="control-group">
              <label>Max Length: {maxLength}</label>
              <input
                type="range"
                min="64"
                max="1024"
                step="32"
                value={maxLength}
                onChange={(e) => setMaxLength(Number(e.target.value))}
              />
            </div>

            <div className="control-group">
              <label>Temperature: {temperature.toFixed(2)}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
              />
            </div>
          </div>

          <button
            className="generate-btn"
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate'}
          </button>
        </div>

        {result && (
          <div className="output-section page-panel">
            <h2>Generated Text</h2>
            <div className="result-box">
              {result}
            </div>
            <button className="copy-btn" onClick={handleCopy}>
              Copy to Clipboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default TextGenerator;
