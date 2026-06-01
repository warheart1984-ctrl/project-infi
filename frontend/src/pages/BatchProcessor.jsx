import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { apiPost, getApiErrorMessage } from '../lib/api';
import { addHistoryEntry } from '../lib/history';
import './BatchProcessor.css';

function BatchProcessor() {
  const [prompts, setPrompts] = useState('');
  const [maxLength, setMaxLength] = useState(512);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

  const handleProcess = async () => {
    const promptList = prompts.split('\n').filter(p => p.trim());
    if (promptList.length === 0) {
      toast.error('Please enter at least one prompt');
      return;
    }

    setLoading(true);
    try {
      const response = await apiPost('/api/batch/text-generate', {
        prompts: promptList,
        max_length: maxLength
      });
      setResults(response.data.results);
      addHistoryEntry({
        type: 'batch',
        prompt: `${promptList.length} prompts`,
        output: `Processed ${response.data.results.length} prompts`,
        model: 'AAIS local API',
      });
      toast.success(`Processed ${promptList.length} prompts successfully!`);
    } catch (error) {
      toast.error(`Error processing batch: ${getApiErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearResults = () => {
    setResults([]);
    setPrompts('');
  };

  return (
    <div className="batch-processor">
      <div className="page-intro">
        <h1>Batch Processor</h1>
        <p>Run several prompts in one request to smoke-test the batch text endpoint.</p>
      </div>
      
      <div className="processor-container">
        <div className="input-section page-panel">
          <label>Enter Prompts (one per line)</label>
          <textarea
            value={prompts}
            onChange={(e) => setPrompts(e.target.value)}
            placeholder="Prompt 1&#10;Prompt 2&#10;Prompt 3..."
            rows="10"
          />

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

          <button
            className="process-btn"
            onClick={handleProcess}
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Process Batch'}
          </button>
        </div>

        {results.length > 0 && (
          <div className="output-section page-panel">
            <div className="results-header">
              <h2>Results ({results.length})</h2>
              <button className="clear-btn" onClick={handleClearResults}>Clear</button>
            </div>
            <div className="results-list">
              {results.map((result, index) => (
                <div key={index} className="result-item">
                  <div className="result-number">#{index + 1}</div>
                  <div className="result-content">
                    {typeof result === 'string' ? result : result.generated_text || JSON.stringify(result)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default BatchProcessor;
