import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import './TextGenerator.css';

function TextGenerator() {
  const [prompt, setPrompt] = useState('');
  const [maxLength, setMaxLength] = useState(512);
  const [temperature, setTemperature] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/text/generate', {
        prompt,
        max_length: maxLength,
        temperature
      });
      setResult(response.data.generated_text);
      toast.success('Text generated successfully!');
    } catch (error) {
      toast.error('Error generating text: ' + error.message);
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
      <h1>Text Generator</h1>
      
      <div className="generator-container">
        <div className="input-section">
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
                min="100"
                max="2000"
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
          <div className="output-section">
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
