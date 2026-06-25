import React from 'react';

export default function FileEditor({ fileContent, onFileContentChange }) {
  return (
    <label className="nova-coding-agent__field nova-coding-agent__editor-field">
      <span>File content</span>
      <textarea
        value={fileContent}
        onChange={(event) => onFileContentChange(event.target.value)}
        spellCheck="false"
      />
    </label>
  );
}
