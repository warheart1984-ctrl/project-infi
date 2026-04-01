import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
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
      const response = await axios.post('http://localhost:5000/api/batch/text-generate', {
        prompts: promptList,
        max_length: maxLength
      });
      setResults(response.data.results);
      toast.success(`Processed ${promptList.length} prompts successfully!`);
    } catch (error) {
      toast.error('Error processing batch: ' + error.message);
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
      <h1>Batch Processor</h1>
      
      <div className="processor-container">
        <div className="input-section">
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
          <div className="output-section">
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
