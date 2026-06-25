import React from 'react';
import { FiFolder, FiSave } from 'react-icons/fi';

export default function FileControls({
  filePath,
  onFilePathChange,
  onOpen,
  onSave,
  busyAction,
}) {
  return (
    <>
      <label className="nova-coding-agent__field">
        <span>File path</span>
        <input value={filePath} onChange={(event) => onFilePathChange(event.target.value)} placeholder="src/example.py" />
      </label>
      <div className="nova-coding-agent__actions">
        <button type="button" onClick={onOpen} disabled={busyAction === 'open'}>
          <FiFolder aria-hidden="true" />
          <span>{busyAction === 'open' ? 'Opening...' : 'Open file'}</span>
        </button>
        <button type="button" onClick={onSave} disabled={busyAction === 'save'}>
          <FiSave aria-hidden="true" />
          <span>{busyAction === 'save' ? 'Saving...' : 'Save file'}</span>
        </button>
      </div>
    </>
  );
}
