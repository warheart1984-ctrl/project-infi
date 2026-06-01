import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { clearHistoryEntries, deleteHistoryEntry, getHistoryEntries } from '../lib/history';
import {
  deleteNovaSessionArchive,
  listNovaSessionArchives,
  openNovaSessionArchive,
  setActiveNovaSessionArchive,
  setPendingNovaSessionArchive,
} from '../lib/novaSessionArchive';
import './History.css';

function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState('archive');
  const [archiveEntries, setArchiveEntries] = useState([]);
  const [archiveListLoading, setArchiveListLoading] = useState(false);
  const [selectedArchiveId, setSelectedArchiveId] = useState('');
  const [selectedArchive, setSelectedArchive] = useState(null);
  const [archivePassphrase, setArchivePassphrase] = useState('');
  const [archiveBusy, setArchiveBusy] = useState(false);

  useEffect(() => {
    setLoading(true);
    try {
      const allEntries = getHistoryEntries();
      const filtered = filter === 'all'
        ? allEntries
        : allEntries.filter((entry) => entry.type === filter);
      setHistory(filtered);
    } catch (error) {
      toast.error(`Error loading history: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    let active = true;

    const loadArchives = async () => {
      setArchiveListLoading(true);
      try {
        const entries = await listNovaSessionArchives();
        if (!active) {
          return;
        }
        setArchiveEntries(entries);
        if (!selectedArchiveId && entries[0]?.id) {
          setSelectedArchiveId(entries[0].id);
        }
        if (selectedArchiveId && !entries.some((entry) => entry.id === selectedArchiveId)) {
          setSelectedArchiveId(entries[0]?.id || '');
          setSelectedArchive(null);
        }
      } catch (error) {
        if (active) {
          toast.error(error.message || 'Could not load the local Nova session archive.');
        }
      } finally {
        if (active) {
          setArchiveListLoading(false);
        }
      }
    };

    loadArchives();

    return () => {
      active = false;
    };
  }, [selectedArchiveId]);

  useEffect(() => {
    let active = true;
    const selectedPreview = archiveEntries.find((entry) => entry.id === selectedArchiveId);

    if (!selectedPreview) {
      setSelectedArchive(null);
      return () => {
        active = false;
      };
    }

    setArchivePassphrase('');
    if (selectedPreview.requiresPassphrase) {
      setSelectedArchive(null);
      return () => {
        active = false;
      };
    }

    const loadSelectedArchive = async () => {
      try {
        const archive = await openNovaSessionArchive(selectedPreview.id);
        if (active) {
          setSelectedArchive(archive);
        }
      } catch (error) {
        if (active) {
          setSelectedArchive(null);
          toast.error(error.message || 'Could not open the selected session archive.');
        }
      }
    };

    loadSelectedArchive();

    return () => {
      active = false;
    };
  }, [archiveEntries, selectedArchiveId]);

  const handleDelete = (id) => {
    const updatedHistory = deleteHistoryEntry(id);
    const filtered = filter === 'all'
      ? updatedHistory
      : updatedHistory.filter((entry) => entry.type === filter);
    setHistory(filtered);
    toast.success('Item deleted');
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      clearHistoryEntries();
      setHistory([]);
      toast.success('History cleared');
    }
  };

  const formatTime = (date) => {
    const now = new Date();
    const diff = now - new Date(date);
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);

    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const selectedPreview = archiveEntries.find((entry) => entry.id === selectedArchiveId) || null;

  const handleUnlockArchive = async () => {
    if (!selectedPreview) {
      return;
    }

    if (!archivePassphrase.trim()) {
      toast.error('Enter the archive passphrase first.');
      return;
    }

    setArchiveBusy(true);
    try {
      const archive = await openNovaSessionArchive(selectedPreview.id, {
        passphrase: archivePassphrase,
      });
      setSelectedArchive(archive);
      toast.success('Archive unlocked on this device.');
    } catch (error) {
      toast.error(error.message || 'That passphrase did not unlock the archive.');
    } finally {
      setArchiveBusy(false);
    }
  };

  const handleLoadArchiveIntoNova = () => {
    if (!selectedArchive) {
      toast.error('Unlock or open the archive before loading it into Nova.');
      return;
    }

    setActiveNovaSessionArchive(selectedArchive);
    setPendingNovaSessionArchive(selectedArchive);
    toast.success('Archive handed off to Nova as document context.');
    navigate('/nova');
  };

  const handleDeleteArchive = async () => {
    if (!selectedPreview) {
      return;
    }

    if (!window.confirm(`Delete "${selectedPreview.title}" from this device?`)) {
      return;
    }

    setArchiveBusy(true);
    try {
      await deleteNovaSessionArchive(selectedPreview.id);
      const nextEntries = await listNovaSessionArchives();
      setArchiveEntries(nextEntries);
      setSelectedArchiveId(nextEntries[0]?.id || '');
      setSelectedArchive(null);
      toast.success('Archive deleted from this device.');
    } catch (error) {
      toast.error(error.message || 'Could not delete this local archive.');
    } finally {
      setArchiveBusy(false);
    }
  };

  return (
    <div className="history">
      <div className="page-intro">
        <h1>Session Archive And Operator Log</h1>
        <p>
          Nova session archives are opt-in, local-only, and loaded back as document context.
          Operator Log stays here too for direct Jarvis chats and subsystem runs from this machine.
        </p>
      </div>

      <div className="history-surface-toggle" role="tablist" aria-label="History surfaces">
        <button
          type="button"
          className={`filter-btn ${activeView === 'archive' ? 'active' : ''}`}
          onClick={() => setActiveView('archive')}
        >
          Session Archive
        </button>
        <button
          type="button"
          className={`filter-btn ${activeView === 'operator' ? 'active' : ''}`}
          onClick={() => setActiveView('operator')}
        >
          Operator Log
        </button>
      </div>

      {activeView === 'archive' ? (
        <div className="archive-shell">
          <section className="archive-list-panel">
            <div className="archive-panel-head">
              <div>
                <h2>Saved Nova sessions</h2>
                <p>Stored only on this device. Loading them does not turn them into memory.</p>
              </div>
              <span className="item-type">LOCAL</span>
            </div>

            {archiveListLoading ? (
              <div className="loading">Loading archive…</div>
            ) : archiveEntries.length === 0 ? (
              <div className="empty-state">
                <p>No session archive yet.</p>
                <p>Use Save Session on Nova home when you want a reopenable local session record.</p>
              </div>
            ) : (
              <div className="archive-list">
                {archiveEntries.map((entry) => (
                  <button
                    key={entry.id}
                    type="button"
                    className={`archive-list-item ${entry.id === selectedArchiveId ? 'active' : ''}`}
                    onClick={() => setSelectedArchiveId(entry.id)}
                  >
                    <strong>{entry.title}</strong>
                    <span>
                      {entry.assistantName} • {entry.messageCount} messages •{' '}
                      {entry.requiresPassphrase ? 'passphrase' : 'device-local'}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="archive-detail-panel">
            {!selectedPreview ? (
              <div className="empty-state">
                <p>Select a saved session archive.</p>
                <p>The detail view lets you inspect, unlock, load, or delete that archive.</p>
              </div>
            ) : (
              <>
                <div className="archive-panel-head">
                  <div>
                    <h2>{selectedPreview.title}</h2>
                    <p>
                      {selectedPreview.assistantName} • {selectedPreview.messageCount} messages •{' '}
                      {selectedPreview.requiresPassphrase ? 'passphrase protected' : 'device-local encrypted'}
                    </p>
                  </div>
                  <span className="item-time">{formatTime(selectedPreview.savedAt)}</span>
                </div>

                {selectedPreview.tags?.length ? (
                  <div className="archive-tag-row">
                    {selectedPreview.tags.map((tag) => (
                      <span key={tag} className="item-type">{tag}</span>
                    ))}
                  </div>
                ) : null}

                {selectedPreview.requiresPassphrase && !selectedArchive ? (
                  <div className="archive-unlock">
                    <p>
                      This archive keeps its transcript behind a passphrase. Unlock it locally to
                      inspect the saved session or load it into Nova.
                    </p>
                    <input
                      type="password"
                      value={archivePassphrase}
                      onChange={(event) => setArchivePassphrase(event.target.value)}
                      placeholder="Enter archive passphrase"
                    />
                    <button
                      type="button"
                      className="nova-button nova-button--primary"
                      onClick={handleUnlockArchive}
                      disabled={archiveBusy}
                    >
                      {archiveBusy ? 'Unlocking…' : 'Unlock Archive'}
                    </button>
                  </div>
                ) : null}

                {selectedArchive ? (
                  <>
                    <div className="archive-preview">
                      <h3>Session excerpt</h3>
                      <p>{selectedArchive.excerpt}</p>
                    </div>

                    <div className="archive-preview">
                      <h3>Transcript preview</h3>
                      <pre>{selectedArchive.transcriptText}</pre>
                    </div>
                  </>
                ) : null}

                <div className="archive-detail-actions">
                  <button
                    type="button"
                    className="nova-button nova-button--primary"
                    onClick={handleLoadArchiveIntoNova}
                    disabled={!selectedArchive || archiveBusy}
                  >
                    Load Into Nova
                  </button>
                  <button
                    type="button"
                    className="nova-button nova-button--ghost"
                    onClick={handleDeleteArchive}
                    disabled={archiveBusy}
                  >
                    Delete Archive
                  </button>
                </div>
              </>
            )}
          </section>
        </div>
      ) : (
        <>
          <div className="history-controls">
            <div className="filter-buttons">
              <button
                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                All
              </button>
              <button
                className={`filter-btn ${filter === 'chat' ? 'active' : ''}`}
                onClick={() => setFilter('chat')}
              >
                Jarvis
              </button>
              <button
                className={`filter-btn ${filter === 'text' ? 'active' : ''}`}
                onClick={() => setFilter('text')}
              >
                Prompt Lab
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
              <p>No private history yet.</p>
              <p>Talk to Jarvis or use one of the tools to start building your local log.</p>
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
                    <p className="item-output"><strong>Output:</strong> {String(item.output).substring(0, 140)}</p>
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
        </>
      )}
    </div>
  );
}

export default History;
