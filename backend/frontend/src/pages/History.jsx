import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import './History.css';

function History() {
  const [history, setHistory] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadHistory();
  }, [filter]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockHistory = [
        {
          id: 1,
          type: 'text',
          prompt: 'Write a story about...',
          output: 'Once upon a time...',
          timestamp: new Date(Date.now() - 3600000),
          model: 'Mistral-7B'
        },
        {
          id: 2,
          type: 'image',
          prompt: 'A beautiful sunset',
          output: 'image.png',
          timestamp: new Date(Date.now() - 7200000),
          model: 'Stable Diffusion 2'
        },
        {
          id: 3,
          type: 'text',
          prompt: 'Explain quantum computing',
          output: 'Quantum computing is...',
          timestamp: new Date(Date.now() - 10800000),
          model: 'Mistral-7B'
        }
      ];
      
      const filtered = filter === 'all' ? mockHistory : mockHistory.filter(h => h.type === filter);
      setHistory(filtered);
    } catch (error) {
      toast.error('Error loading history: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (id) => {
    setHistory(history.filter(h => h.id !== id));
    toast.success('Item deleted');
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      setHistory([]);
      toast.success('History cleared');
    }
  };

  const formatTime = (date) => {
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  return (
    <div className="history">
      <h1>Generation History</h1>
      
      <div className="history-controls">
        <div className="filter-buttons">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={`filter-btn ${filter === 'text' ? 'active' : ''}`}
            onClick={() => setFilter('text')}
          >
            Text
          </button>
          <button
            className={`filter-btn ${filter === 'image' ? 'active' : ''}`}
            onClick={() => setFilter('image')}
          >
            Images
          </button>
          <button
            className={`filter-btn ${filter === 'audio' ? 'active' : ''}`}
            onClick={() => setFilter('audio')}
          >
            Audio
          </button>
        </div>
        {history.length > 0 && (
          <button className="clear-all-btn" onClick={handleClearAll}>
            Clear All
          </button>
        )}
      </div>

      {loading ? (
        <div className="loading">Loading history...</div>
      ) : history.length === 0 ? (
        <div className="empty-state">
          <p>📭 No history yet</p>
          <p>Start generating content to see it here</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className={`history-item ${item.type}`}>
              <div className="item-header">
                <span className="item-type">{item.type.toUpperCase()}</span>
                <span className="item-time">{formatTime(item.timestamp)}</span>
              </div>
              <div className="item-content">
                <p className="item-prompt"><strong>Prompt:</strong> {item.prompt}</p>
                <p className="item-model"><strong>Model:</strong> {item.model}</p>
                {item.type === 'text' && (
                  <p className="item-output"><strong>Output:</strong> {item.output.substring(0, 100)}...</p>
                )}
              </div>
              <button
                className="delete-btn"
                onClick={() => handleDelete(item.id)}
                title="Delete"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default History;
