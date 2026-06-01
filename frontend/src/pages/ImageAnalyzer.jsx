import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import { addHistoryEntry } from '../lib/history';
import {
  getActiveJarvisSessionId,
  getJarvisProfile,
  setActiveJarvisSessionId,
  setPendingJarvisDraft,
} from '../lib/jarvis';
import './ImageAnalyzer.css';

function ImageAnalyzer() {
  const navigate = useNavigate();
  const [selectedImage, setSelectedImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [useDocumentVision, setUseDocumentVision] = useState(false);
  const [useUiVision, setUseUiVision] = useState(false);
  const [useOperatorAssist, setUseOperatorAssist] = useState(false);
  const [operatorContext, setOperatorContext] = useState('');
  const [actionBusyId, setActionBusyId] = useState('');
  const [actionResult, setActionResult] = useState(null);
  const [previewLoadingPath, setPreviewLoadingPath] = useState('');
  const [matchedFilePreview, setMatchedFilePreview] = useState(null);

  const resetOperatorFollowups = () => {
    setActionResult(null);
    setPreviewLoadingPath('');
    setMatchedFilePreview(null);
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      resetOperatorFollowups();
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage) {
      toast.error('Please select an image');
      return;
    }

    setLoading(true);
    resetOperatorFollowups();
    const formData = new FormData();
    formData.append('image', selectedImage);
    formData.append('include_ocr', String(useDocumentVision));
    formData.append('include_ui', String(useUiVision));
    formData.append('include_operator_assist', String(useOperatorAssist));
    if (operatorContext.trim()) {
      formData.append('operator_context', operatorContext.trim());
    }

    try {
      const response = await apiPost('/api/image/analyze', formData);
      setAnalysis(response.data);
      addHistoryEntry({
        type: 'image',
        prompt: selectedImage.name,
        output: response.data.description,
        model: 'AAIS local API',
      });
      toast.success('Image analyzed successfully!');
    } catch (error) {
      toast.error(`Error analyzing image: ${getApiErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const ensureJarvisSession = async () => {
    const activeSessionId = getActiveJarvisSessionId();
    if (activeSessionId) {
      try {
        await apiGet(`/api/chat/sessions/${activeSessionId}`);
        return activeSessionId;
      } catch (error) {
        // Fall through and create a fresh session if the stored one expired.
      }
    }

    const profile = getJarvisProfile();
    const response = await apiPost('/api/chat/sessions', {
      system_prompt: profile.systemPrompt,
      persona_mode: profile.personaMode,
      response_mode: profile.responseMode,
    });
    setActiveJarvisSessionId(response.data.session_id);
    return response.data.session_id;
  };

  const buildJarvisHandoffPrompt = () => {
    if (!analysis) {
      return '';
    }

    const assist = analysis.operator_assist || {};
    const matchLines = (assist.workspace_context?.results || [])
      .slice(0, 3)
      .map((result) => `- ${result.relative_path}: ${result.snippet || 'workspace match'}`);
    const nextStepLines = (assist.next_steps || []).slice(0, 3).map((step) => `- ${step}`);
    const debugSignals = assist.debug_signals?.length
      ? assist.debug_signals.join(', ')
      : 'none';

    return [
      'Use this screenshot debugging context and help me reason through the issue.',
      `Image summary: ${analysis.description}`,
      assist.summary ? `Operator assist: ${assist.summary}` : '',
      assist.workspace_query ? `Workspace query: ${assist.workspace_query}` : '',
      `Debug signals: ${debugSignals}`,
      matchLines.length ? 'Best workspace matches:\n' + matchLines.join('\n') : '',
      nextStepLines.length ? 'Current next steps:\n' + nextStepLines.join('\n') : '',
      'Give me the most likely cause, the first file to inspect, and the safest next move.',
    ]
      .filter(Boolean)
      .join('\n\n');
  };

  const handleOpenInJarvis = () => {
    if (!analysis?.operator_assist) {
      toast.error('Run screenshot-to-action first.');
      return;
    }

    setPendingJarvisDraft({
      text: buildJarvisHandoffPrompt(),
      source: 'image-analyzer',
    });
    navigate('/');
  };

  const handleRunSuggestedAction = async () => {
    const action = analysis?.operator_assist?.suggested_action;
    if (!action?.id) {
      toast.error('No safe action was suggested for this screenshot.');
      return;
    }

    const approved = window.confirm(
      `Run "${action.label}"?\n\nThis uses the guarded local action runner.\n\nCommand: ${action.command_preview || action.id}`,
    );
    if (!approved) {
      return;
    }

    setActionBusyId(action.id);
    try {
      const sessionId = await ensureJarvisSession();
      const profile = getJarvisProfile();
      const response = await apiPost(`/api/chat/sessions/${sessionId}/actions/execute`, {
        action_id: action.id,
        approved: true,
        persona_mode: profile.personaMode,
        response_mode: profile.responseMode,
      });
      setActionResult(response.data.tool_result || null);
      addHistoryEntry({
        type: 'chat',
        prompt: `Image operator action: ${action.label}`,
        output: response.data.response || response.data.tool_result?.summary || '',
        model: 'Jarvis operator',
      });
      toast.success(response.data.tool_result?.summary || `${action.label} completed`);
    } catch (error) {
      toast.error(`Could not run action: ${getApiErrorMessage(error)}`);
    } finally {
      setActionBusyId('');
    }
  };

  const handlePreviewMatchedFile = async (relativePath) => {
    if (!relativePath) {
      return;
    }

    setPreviewLoadingPath(relativePath);
    try {
      const response = await apiGet('/api/jarvis/workspace/file', {
        params: { path: relativePath, max_chars: 2200 },
      });
      setMatchedFilePreview(response.data);
    } catch (error) {
      toast.error(`Could not open file preview: ${getApiErrorMessage(error)}`);
    } finally {
      setPreviewLoadingPath('');
    }
  };

  return (
    <div className="image-analyzer">
      <div className="page-intro">
        <h1>Image Analyzer</h1>
        <p>Upload an image and inspect the structured response returned by the local API.</p>
      </div>
      
      <div className="analyzer-container">
        <div className="input-section page-panel">
          <label>Select Image</label>
          <div className="feature-note">
            Vision analysis is wired for real use now. The result is grounded with CLIP label ranking and color extraction instead of a generic made-up caption.
          </div>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={useDocumentVision}
              onChange={(event) => setUseDocumentVision(event.target.checked)}
            />
            <span>Request document vision (OCR)</span>
          </label>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={useUiVision}
              onChange={(event) => setUseUiVision(event.target.checked)}
            />
            <span>Request screenshot / UI understanding</span>
          </label>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={useOperatorAssist}
              onChange={(event) => setUseOperatorAssist(event.target.checked)}
            />
            <span>Request screenshot-to-action operator assist</span>
          </label>
          {useOperatorAssist && (
            <div className="analysis-section-block">
              <label htmlFor="operator-context" className="context-label">
                Operator hint
              </label>
              <textarea
                id="operator-context"
                className="operator-context-input"
                rows="4"
                value={operatorContext}
                onChange={(event) => setOperatorContext(event.target.value)}
                placeholder="Optional: tell Nova what to look for, like 'debug the chat route in api.py' or 'this mobile screen looks broken.'"
              />
              <div className="context-note">
                Jarvis will automatically pull OCR and UI clues when this assist mode is on.
              </div>
            </div>
          )}
          <div className="image-upload">
            {preview ? (
              <img src={preview} alt="Preview" className="preview-image" />
            ) : (
              <div className="upload-placeholder">
                <p>📷 Click to select an image</p>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="file-input"
            />
          </div>

          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={loading || !selectedImage}
          >
            {loading ? 'Analyzing...' : 'Analyze Image'}
          </button>
        </div>

        {analysis && (
          <div className="output-section page-panel">
            <h2>Analysis Result</h2>
            <div className="analysis-box">
              <p>{analysis.description}</p>
              <div className="analysis-meta">
                <span>{analysis.analysis_method}</span>
                <span>
                  {analysis.image_size?.width} x {analysis.image_size?.height}
                </span>
                <span>{analysis.image_size?.orientation}</span>
              </div>
              {!!analysis.top_matches?.length && (
                <div className="analysis-section">
                  <h3>Top Visual Matches</h3>
                  <div className="token-grid">
                    {analysis.top_matches.map((match) => (
                      <span key={match.label} className="analysis-token">
                        {match.label} {Math.round(match.score * 100)}%
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {!!analysis.dominant_colors?.length && (
                <div className="analysis-section">
                  <h3>Dominant Colors</h3>
                  <div className="color-grid">
                    {analysis.dominant_colors.map((color) => (
                      <div key={color.hex} className="color-chip">
                        <span
                          className="color-swatch"
                          style={{ backgroundColor: color.hex }}
                        />
                        <span>{color.hex}</span>
                        <span>{Math.round(color.share * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {!!analysis.ocr && (
                <div className="analysis-section">
                  <h3>Document Vision</h3>
                  <div className="ocr-summary">
                    {analysis.ocr.summary}
                  </div>
                  <div className="analysis-meta">
                    <span>{analysis.ocr.status}</span>
                    <span>{analysis.ocr.engine}</span>
                    {analysis.ocr.word_count > 0 && (
                      <span>{analysis.ocr.word_count} words</span>
                    )}
                    {analysis.ocr.average_confidence != null && (
                      <span>{Math.round(analysis.ocr.average_confidence)}% confidence</span>
                    )}
                  </div>
                  {!!analysis.ocr.text_preview && (
                    <pre className="ocr-preview">{analysis.ocr.text_preview}</pre>
                  )}
                </div>
              )}
              {!!analysis.ui && (
                <div className="analysis-section">
                  <h3>UI Understanding</h3>
                  <div className="ocr-summary">
                    {analysis.ui.summary}
                  </div>
                  <div className="analysis-meta">
                    <span>{analysis.ui.status}</span>
                    {analysis.ui.surface_type && <span>{analysis.ui.surface_type}</span>}
                    {analysis.ui.platform_hint && <span>{analysis.ui.platform_hint}</span>}
                    {analysis.ui.theme && <span>{analysis.ui.theme} theme</span>}
                    {analysis.ui.panel_estimate && <span>{analysis.ui.panel_estimate} regions</span>}
                    {analysis.ui.density_label && <span>{analysis.ui.density_label} density</span>}
                    {analysis.ui.code_language && <span>{analysis.ui.code_language}</span>}
                  </div>
                  {!!analysis.ui.layout_clues?.length && (
                    <div className="analysis-section-block">
                      <strong>Layout clues</strong>
                      <div className="token-grid">
                        {analysis.ui.layout_clues.map((clue) => (
                          <span key={clue} className="analysis-token">
                            {clue}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {!!analysis.ui.readable_targets?.length && (
                    <div className="analysis-section-block">
                      <strong>Readable targets</strong>
                      <div className="token-grid">
                        {analysis.ui.readable_targets.map((target) => (
                          <span key={target} className="analysis-token">
                            {target}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              {!!analysis.operator_assist && (
                <div className="analysis-section">
                  <h3>Screenshot-To-Action</h3>
                  <div className="ocr-summary">
                    {analysis.operator_assist.summary}
                  </div>
                  <div className="analysis-meta">
                    {analysis.operator_assist.surface_type && (
                      <span>{analysis.operator_assist.surface_type}</span>
                    )}
                    {analysis.operator_assist.code_language && (
                      <span>{analysis.operator_assist.code_language}</span>
                    )}
                    {!!analysis.operator_assist.debug_signals?.length && (
                      <span>{analysis.operator_assist.debug_signals.length} debug signals</span>
                    )}
                  </div>
                  {!!analysis.operator_assist.workspace_query && (
                    <div className="analysis-section-block">
                      <strong>Workspace query</strong>
                      <div className="context-note">{analysis.operator_assist.workspace_query}</div>
                    </div>
                  )}
                  {!!analysis.operator_assist.suggested_action && (
                    <div className="workspace-result-card">
                      <strong>{analysis.operator_assist.suggested_action.label}</strong>
                      <p>{analysis.operator_assist.action_reason}</p>
                      <code>{analysis.operator_assist.suggested_action.command_preview}</code>
                    </div>
                  )}
                  <div className="jarvis-inline-actions screenshot-action-row">
                    {!!analysis.operator_assist.suggested_action && (
                      <button
                        type="button"
                        className="inline-card-action"
                        onClick={handleRunSuggestedAction}
                        disabled={actionBusyId === analysis.operator_assist.suggested_action.id}
                      >
                        {actionBusyId === analysis.operator_assist.suggested_action.id
                          ? 'Running...'
                          : 'Approve and Run'}
                      </button>
                    )}
                    {!!analysis.operator_assist.workspace_context?.results?.[0]?.relative_path && (
                      <button
                        type="button"
                        className="inline-card-action"
                        onClick={() => handlePreviewMatchedFile(
                          analysis.operator_assist.workspace_context.results[0].relative_path,
                        )}
                        disabled={
                          previewLoadingPath === analysis.operator_assist.workspace_context.results[0].relative_path
                        }
                      >
                        {previewLoadingPath === analysis.operator_assist.workspace_context.results[0].relative_path
                          ? 'Opening File...'
                          : 'Open Strongest File'}
                      </button>
                    )}
                    <button
                      type="button"
                      className="inline-card-action"
                      onClick={handleOpenInJarvis}
                    >
                      Open in Nova
                    </button>
                  </div>
                  {!!analysis.operator_assist.debug_signals?.length && (
                    <div className="analysis-section-block">
                      <strong>Debug signals</strong>
                      <div className="token-grid">
                        {analysis.operator_assist.debug_signals.map((signal) => (
                          <span key={signal} className="analysis-token">
                            {signal}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {!!analysis.operator_assist.workspace_context?.results?.length && (
                    <div className="analysis-section-block">
                      <strong>Workspace matches</strong>
                      <div className="workspace-result-list">
                        {analysis.operator_assist.workspace_context.results.map((result) => (
                          <div key={result.relative_path} className="workspace-result-card">
                            <div className="workspace-result-path">{result.relative_path}</div>
                            <div className="context-note">{result.snippet}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {!!matchedFilePreview && (
                    <div className="analysis-section-block">
                      <strong>Matched file preview</strong>
                      <div className="workspace-result-card">
                        <div className="workspace-result-path">{matchedFilePreview.relative_path}</div>
                        <pre className="ocr-preview">{matchedFilePreview.content}</pre>
                      </div>
                    </div>
                  )}
                  {!!actionResult && (
                    <div className="analysis-section-block">
                      <strong>Last action result</strong>
                      <div className={`workspace-result-card ${actionResult.status === 'failed' ? 'action-failed' : ''}`}>
                        <div className="workspace-result-path">{actionResult.action?.label || 'Safe action'}</div>
                        <div className="analysis-meta">
                          <span>{actionResult.status}</span>
                          <span>exit {actionResult.exit_code}</span>
                        </div>
                        <div className="context-note">{actionResult.summary}</div>
                        {!!(actionResult.stdout || actionResult.stderr) && (
                          <pre className="ocr-preview">{actionResult.stderr || actionResult.stdout}</pre>
                        )}
                      </div>
                    </div>
                  )}
                  {!!analysis.operator_assist.next_steps?.length && (
                    <div className="analysis-section-block">
                      <strong>Next steps</strong>
                      <ul className="analysis-list">
                        {analysis.operator_assist.next_steps.map((step) => (
                          <li key={step}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageAnalyzer;
