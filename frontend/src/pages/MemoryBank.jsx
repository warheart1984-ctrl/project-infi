import React, { useCallback, useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import {
  FiBookmark,
  FiEdit3,
  FiPlus,
  FiRefreshCw,
  FiShield,
  FiTrash2,
} from 'react-icons/fi';
import { Link } from 'react-router-dom';
import {
  addMemory,
  addOverrideMemory,
  deleteMemory,
  getMemoryBoard,
  getMemories,
  updateMemory,
} from '../api/memory';
import { getApiErrorMessage } from '../lib/api';
import './MemoryBank.css';

const COMMON_CATEGORIES = [
  'general',
  'identity',
  'operator',
  'project',
  'coding',
  'preference',
  'behavior',
  'override',
];

function createDraft(overrides = {}) {
  return {
    content: '',
    category: 'general',
    priority: 50,
    active: true,
    tags: '',
    pinned: false,
    override: false,
    ...overrides,
  };
}

function clipText(text, limit = 120) {
  const cleaned = String(text || '').replace(/\s+/g, ' ').trim();
  if (cleaned.length <= limit) {
    return cleaned;
  }
  return `${cleaned.slice(0, limit - 3).trimEnd()}...`;
}

function formatStamp(timestamp) {
  if (!timestamp) {
    return 'Unknown';
  }
  const value = new Date(timestamp);
  if (Number.isNaN(value.getTime())) {
    return 'Unknown';
  }
  return value.toLocaleString();
}

function formatRelativeTime(timestamp) {
  if (!timestamp) {
    return 'Unknown';
  }
  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.max(0, Math.floor(diff / 60000));
  if (minutes < 1) {
    return 'Just now';
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function MemoryBank() {
  const [memories, setMemories] = useState([]);
  const [memoryBoard, setMemoryBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [savingCreate, setSavingCreate] = useState(false);
  const [savingEditor, setSavingEditor] = useState(false);
  const [searchDraft, setSearchDraft] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [sortMode, setSortMode] = useState('priority');
  const [selectedMemoryId, setSelectedMemoryId] = useState('');
  const [createState, setCreateState] = useState(() => createDraft());
  const [editorState, setEditorState] = useState(() => createDraft());

  const loadMemories = useCallback(async (showSpinner = true) => {
    if (showSpinner) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    try {
      const [memoryResponse, boardResponse] = await Promise.all([
        getMemories({
          limit: 48,
          query: searchQuery || undefined,
          category: categoryFilter || undefined,
          active: activeFilter === 'all' ? undefined : String(activeFilter === 'active'),
          sort: sortMode,
        }),
        getMemoryBoard(),
      ]);
      const nextMemories = memoryResponse.data.memories || [];
      const nextBoard = boardResponse.data.memory_board || null;
      setMemories(nextMemories);
      setMemoryBoard(nextBoard);
      setSelectedMemoryId((current) => (
        current && nextMemories.some((memory) => memory.id === current)
          ? current
          : (nextMemories[0]?.id || '')
      ));
    } catch (error) {
      toast.error(`Could not load memories: ${getApiErrorMessage(error)}`);
      setMemories([]);
      setMemoryBoard(null);
      setSelectedMemoryId('');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFilter, categoryFilter, searchQuery, sortMode]);

  useEffect(() => {
    loadMemories(true);
  }, [loadMemories]);

  const selectedMemory = useMemo(
    () => memories.find((memory) => memory.id === selectedMemoryId) || null,
    [memories, selectedMemoryId],
  );

  useEffect(() => {
    if (!selectedMemory) {
      setEditorState(createDraft());
      return;
    }

    setEditorState(createDraft({
      content: selectedMemory.content || selectedMemory.text || '',
      category: selectedMemory.category || 'general',
      priority: selectedMemory.priority ?? 50,
      active: selectedMemory.active !== false,
      tags: (selectedMemory.tags || []).join(', '),
      pinned: Boolean(selectedMemory.pinned),
      override: Boolean(selectedMemory.override),
    }));
  }, [selectedMemory]);

  const availableCategories = useMemo(() => {
    const categories = new Set(COMMON_CATEGORIES);
    memories.forEach((memory) => {
      if (memory.category) {
        categories.add(memory.category);
      }
    });
    return Array.from(categories);
  }, [memories]);

  const summary = useMemo(() => {
    const activeCount = memories.filter((memory) => memory.active !== false).length;
    const overrideCount = memories.filter((memory) => memory.override).length;
    const pinnedCount = memories.filter((memory) => memory.pinned).length;
    return {
      total: memories.length,
      active: activeCount,
      inactive: Math.max(memories.length - activeCount, 0),
      overrides: overrideCount,
      pinned: pinnedCount,
      boardInstalled: memoryBoard?.installed_slots ?? 0,
    };
  }, [memories, memoryBoard]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setSearchQuery(searchDraft.trim());
  };

  const handleRefresh = () => {
    loadMemories(false);
  };

  const handleCreateMemory = async (event) => {
    event.preventDefault();
    const content = createState.content.trim();
    if (!content || savingCreate) {
      return;
    }

    const payload = {
      content,
      category: createState.category.trim() || 'general',
      priority: Number(createState.priority) || 50,
      active: createState.active,
      tags: createState.tags,
      pinned: createState.pinned,
    };

    setSavingCreate(true);
    try {
      const response = createState.override
        ? await addOverrideMemory(payload)
        : await addMemory({ ...payload, override: false });
      const created = response.data;
      setCreateState(createDraft());
      await loadMemories(false);
      setSelectedMemoryId(created?.id || '');
      toast.success(createState.override ? 'Override saved' : 'Memory saved');
    } catch (error) {
      toast.error(`Could not save memory: ${getApiErrorMessage(error)}`);
    } finally {
      setSavingCreate(false);
    }
  };

  const handleSaveSelected = async (event) => {
    event.preventDefault();
    if (!selectedMemory || savingEditor) {
      return;
    }
    const content = editorState.content.trim();
    if (!content) {
      toast.error('Memory content is required.');
      return;
    }

    setSavingEditor(true);
    try {
      await updateMemory(selectedMemory.id, {
        content,
        category: editorState.category.trim() || 'general',
        priority: Number(editorState.priority) || 50,
        active: editorState.active,
        tags: editorState.tags,
        pinned: editorState.pinned,
        override: editorState.override,
      });
      await loadMemories(false);
      toast.success('Memory updated');
    } catch (error) {
      toast.error(`Could not update memory: ${getApiErrorMessage(error)}`);
    } finally {
      setSavingEditor(false);
    }
  };

  const handleDeleteMemory = async (memoryId) => {
    try {
      await deleteMemory(memoryId);
      await loadMemories(false);
      toast.success('Memory deleted');
    } catch (error) {
      toast.error(`Could not delete memory: ${getApiErrorMessage(error)}`);
    }
  };

  const handleToggleActive = async (memory) => {
    try {
      await updateMemory(memory.id, {
        active: memory.active === false,
      });
      await loadMemories(false);
      toast.success(memory.active === false ? 'Memory reactivated' : 'Memory deactivated');
    } catch (error) {
      toast.error(`Could not change memory state: ${getApiErrorMessage(error)}`);
    }
  };

  return (
    <section className="memory-bank">
      <div className="page-intro">
        <h1>Memory Bank</h1>
        <p>
          Long-term Jarvis memory is editable here. Use it to rewrite rules, deactivate stale notes,
          add higher-priority overrides, and keep durable operator truth separate from chat noise.
        </p>
      </div>

      <div className="memory-bank-summary">
        <div className="memory-stat page-panel">
          <span>Total</span>
          <strong>{summary.total}</strong>
        </div>
        <div className="memory-stat page-panel">
          <span>Active</span>
          <strong>{summary.active}</strong>
        </div>
        <div className="memory-stat page-panel">
          <span>Board Cards</span>
          <strong>{summary.boardInstalled}</strong>
        </div>
        <div className="memory-stat page-panel">
          <span>Overrides</span>
          <strong>{summary.overrides}</strong>
        </div>
      </div>

      {memoryBoard && (
        <div className="memory-board-panel page-panel">
          <div className="memory-panel-header">
            <div>
              <span>Installed Board</span>
              <h2>{memoryBoard.board?.board_label || 'Memory Board'}</h2>
              <p className="memory-board-copy">
                {memoryBoard.board?.summary || 'Memory Bank is linked to the currently installed board snapshot.'}
              </p>
            </div>
            <div className="memory-board-inline-stats">
              <div className="memory-board-inline-stat">
                <span>Version</span>
                <strong>{memoryBoard.board?.board_version || 'Unknown'}</strong>
              </div>
              <div className="memory-board-inline-stat">
                <span>Records</span>
                <strong>{memoryBoard.classified_record_count ?? 0}</strong>
              </div>
              <div className="memory-board-inline-stat">
                <span>Pinned</span>
                <strong>{summary.pinned}</strong>
              </div>
            </div>
          </div>
          <div className="memory-board-links">
            {(memoryBoard.board?.linked_subsystems || []).map((subsystem) => (
              <span key={subsystem} className="memory-board-chip">
                {subsystem}
              </span>
            ))}
          </div>
          <div className="memory-board-slots">
            {(memoryBoard.slots || []).map((slot) => {
              const module = slot.module;
              return (
                <article
                  key={slot.slot_id}
                  className={`memory-board-slot ${slot.reserved ? 'reserved' : ''} ${module ? 'installed' : ''}`}
                >
                  <div className="memory-board-slot-topline">
                    <div>
                      <span>{slot.slot_name}</span>
                      <strong>{module?.display_name || 'Reserved Slot'}</strong>
                    </div>
                    <span className="memory-board-slot-count">{slot.record_count ?? 0} records</span>
                  </div>
                  <p className="memory-board-slot-copy">
                    {module?.summary || 'Inactive slot reserved for future board growth.'}
                  </p>
                  <div className="memory-board-slot-meta">
                    <span>{module?.module_id || slot.accepted_class}</span>
                    <span>{module?.trust_class || 'reserved'}</span>
                    <span>{module?.linked_subsystem || 'future_slot'}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}

      <div className="memory-bank-toolbar page-panel">
        <form className="memory-search" onSubmit={handleSearchSubmit}>
          <input
            type="text"
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            placeholder="Search memory content, category, or tags"
          />
          <button type="submit" className="memory-toolbar-button">Search</button>
        </form>
        <div className="memory-filter-grid">
          <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
            <option value="">All categories</option>
            {availableCategories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          <select value={activeFilter} onChange={(event) => setActiveFilter(event.target.value)}>
            <option value="all">All states</option>
            <option value="active">Active only</option>
            <option value="inactive">Inactive only</option>
          </select>
          <select value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
            <option value="priority">Sort by priority</option>
            <option value="recency">Sort by recency</option>
            <option value="created">Sort by created date</option>
          </select>
          <button type="button" className="memory-toolbar-button secondary" onClick={handleRefresh}>
            <FiRefreshCw />
            {refreshing ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="memory-bank-grid">
        <div className="memory-panel page-panel">
          <div className="memory-panel-header">
            <div>
              <span>Memory List</span>
              <h2>Durable notes and overrides</h2>
            </div>
            <Link className="memory-panel-link" to="/">Back to Nova</Link>
          </div>
          {loading ? (
            <div className="memory-empty">Loading memories…</div>
          ) : memories.length === 0 ? (
            <div className="memory-empty">No memories match this view yet.</div>
          ) : (
            <div className="memory-records">
              {memories.map((memory) => (
                <article
                  key={memory.id}
                  className={`memory-record ${memory.id === selectedMemoryId ? 'selected' : ''} ${memory.active === false ? 'inactive' : ''}`}
                >
                  <button
                    type="button"
                    className="memory-record-main"
                    onClick={() => setSelectedMemoryId(memory.id)}
                  >
                    <div className="memory-record-topline">
                      <strong>{clipText(memory.content || memory.text)}</strong>
                      <span className="memory-priority">P{memory.priority ?? 50}</span>
                    </div>
                    <div className="memory-record-meta">
                      <span>{memory.category || 'general'}</span>
                      <span>{memory.active === false ? 'Inactive' : 'Active'}</span>
                      <span>{formatRelativeTime(memory.updated_at)}</span>
                    </div>
                    <div className="memory-badges">
                      {memory.pinned && <span className="status-pill connected">Pinned</span>}
                      {memory.override && <span className="status-pill warning">Override</span>}
                    </div>
                  </button>
                  <div className="memory-record-actions">
                    <button type="button" className="memory-icon-button" onClick={() => setSelectedMemoryId(memory.id)}>
                      <FiEdit3 />
                    </button>
                    <button type="button" className="memory-icon-button" onClick={() => handleToggleActive(memory)}>
                      {memory.active === false ? 'Enable' : 'Pause'}
                    </button>
                    <button type="button" className="memory-icon-button danger" onClick={() => handleDeleteMemory(memory.id)}>
                      <FiTrash2 />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="memory-panel page-panel">
          <div className="memory-panel-header">
            <div>
              <span>Memory Editor</span>
              <h2>Rewrite or deactivate a saved memory</h2>
            </div>
          </div>
          {!selectedMemory ? (
            <div className="memory-empty">Pick a memory from the list to edit it.</div>
          ) : (
            <form className="memory-form" onSubmit={handleSaveSelected}>
              <label>
                <span>Content</span>
                <textarea
                  value={editorState.content}
                  onChange={(event) => setEditorState((current) => ({ ...current, content: event.target.value }))}
                  rows="10"
                />
              </label>
              <div className="memory-form-grid">
                <label>
                  <span>Category</span>
                  <input
                    list="memory-category-options"
                    type="text"
                    value={editorState.category}
                    onChange={(event) => setEditorState((current) => ({ ...current, category: event.target.value }))}
                  />
                </label>
                <label>
                  <span>Priority</span>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editorState.priority}
                    onChange={(event) => setEditorState((current) => ({ ...current, priority: event.target.value }))}
                  />
                </label>
              </div>
              <label>
                <span>Tags</span>
                <input
                  type="text"
                  value={editorState.tags}
                  onChange={(event) => setEditorState((current) => ({ ...current, tags: event.target.value }))}
                  placeholder="coding, jarvis, project"
                />
              </label>
              <div className="memory-toggle-row">
                <button
                  type="button"
                  className={`memory-toggle ${editorState.active ? 'active' : ''}`}
                  onClick={() => setEditorState((current) => ({ ...current, active: !current.active }))}
                >
                  <FiShield />
                  {editorState.active ? 'Active' : 'Inactive'}
                </button>
                <button
                  type="button"
                  className={`memory-toggle ${editorState.pinned ? 'active' : ''}`}
                  onClick={() => setEditorState((current) => ({ ...current, pinned: !current.pinned }))}
                >
                  <FiBookmark />
                  {editorState.pinned ? 'Pinned' : 'Pin'}
                </button>
                <button
                  type="button"
                  className={`memory-toggle ${editorState.override ? 'warning' : ''}`}
                  onClick={() => setEditorState((current) => ({ ...current, override: !current.override }))}
                >
                  Override Rule
                </button>
              </div>
              <div className="memory-form-footer">
                <div className="memory-stamp-group">
                  <span>Created {formatStamp(selectedMemory.created_at)}</span>
                  <span>Updated {formatStamp(selectedMemory.updated_at)}</span>
                </div>
                <button type="submit" className="memory-primary-button" disabled={savingEditor}>
                  <FiEdit3 />
                  {savingEditor ? 'Saving' : 'Save Memory'}
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="memory-panel page-panel">
          <div className="memory-panel-header">
            <div>
              <span>Add Memory</span>
              <h2>Create durable rules or new overrides</h2>
            </div>
          </div>
          <form className="memory-form" onSubmit={handleCreateMemory}>
            <label>
              <span>Content</span>
              <textarea
                value={createState.content}
                onChange={(event) => setCreateState((current) => ({ ...current, content: event.target.value }))}
                placeholder="Save a durable rule, preference, system note, or correction."
                rows="8"
              />
            </label>
            <div className="memory-form-grid">
              <label>
                <span>Category</span>
                <input
                  list="memory-category-options"
                  type="text"
                  value={createState.category}
                  onChange={(event) => setCreateState((current) => ({ ...current, category: event.target.value }))}
                />
              </label>
              <label>
                <span>Priority</span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={createState.priority}
                  onChange={(event) => setCreateState((current) => ({ ...current, priority: event.target.value }))}
                />
              </label>
            </div>
            <label>
              <span>Tags</span>
              <input
                type="text"
                value={createState.tags}
                onChange={(event) => setCreateState((current) => ({ ...current, tags: event.target.value }))}
                placeholder="jarvis, project, coding"
              />
            </label>
            <div className="memory-toggle-row">
              <button
                type="button"
                className={`memory-toggle ${createState.active ? 'active' : ''}`}
                onClick={() => setCreateState((current) => ({ ...current, active: !current.active }))}
              >
                <FiShield />
                {createState.active ? 'Active' : 'Inactive'}
              </button>
              <button
                type="button"
                className={`memory-toggle ${createState.pinned ? 'active' : ''}`}
                onClick={() => setCreateState((current) => ({ ...current, pinned: !current.pinned }))}
              >
                <FiBookmark />
                {createState.pinned ? 'Pinned' : 'Pin'}
              </button>
              <button
                type="button"
                className={`memory-toggle ${createState.override ? 'warning' : ''}`}
                onClick={() => setCreateState((current) => ({ ...current, override: !current.override }))}
              >
                Override Rule
              </button>
            </div>
            <button type="submit" className="memory-primary-button" disabled={savingCreate}>
              {createState.override ? <FiShield /> : <FiPlus />}
              {savingCreate ? 'Saving' : (createState.override ? 'Create Override' : 'Create Memory')}
            </button>
          </form>
        </div>
      </div>

      <datalist id="memory-category-options">
        {availableCategories.map((category) => (
          <option key={category} value={category} />
        ))}
      </datalist>
    </section>
  );
}

export default MemoryBank;
