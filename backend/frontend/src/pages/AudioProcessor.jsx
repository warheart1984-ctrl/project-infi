import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import './AudioProcessor.css';

function AudioProcessor() {
  const [selectedAudio, setSelectedAudio] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [features, setFeatures] = useState(null);
  const [silentSegments, setSilentSegments] = useState([]);

  const handleAudioSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedAudio(file);
      const audio = new Audio(URL.createObjectURL(file));
      setPreview(audio);
    }
  };

  const handleExtractFeatures = async () => {
    if (!selectedAudio) {
      toast.error('Please select an audio file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('audio', selectedAudio);

    try {
      const response = await axios.post('http://localhost:5000/api/audio/extract-features', formData);
      setFeatures(response.data);
      toast.success('Features extracted successfully!');
    } catch (error) {
      toast.error('Error extracting features: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDetectSilence = async () => {
    if (!selectedAudio) {
      toast.error('Please select an audio file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('audio', selectedAudio);

    try {
      const response = await axios.post('http://localhost:5000/api/audio/detect-silence', formData);
      setSilentSegments(response.data.silent_segments);
      toast.success('Silence detected successfully!');
    } catch (error) {
      toast.error('Error detecting silence: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="audio-processor">
      <h1>Audio Processor</h1>
      
      <div className="processor-container">
        <div className="input-section">
          <label>Select Audio File</label>
          <div className="audio-upload">
            {preview ? (
              <div className="audio-player">
                <audio controls style={{ width: '100%' }}>
                  <source src={URL.createObjectURL(selectedAudio)} type={selectedAudio.type} />
                </audio>
                <p className="file-name">{selectedAudio.name}</p>
              </div>
            ) : (
              <div className="upload-placeholder">
                <p>🎵 Click to select an audio file</p>
              </div>
            )}
            <input
              type="file"
              accept="audio/*"
              onChange={handleAudioSelect}
              className="file-input"
            />
          </div>

          <div className="button-group">
            <button
              className="process-btn"
              onClick={handleExtractFeatures}
              disabled={loading || !selectedAudio}
            >
              {loading ? 'Processing...' : 'Extract Features'}
            </button>
            <button
              className="process-btn secondary"
              onClick={handleDetectSilence}
              disabled={loading || !selectedAudio}
            >
              {loading ? 'Processing...' : 'Detect Silence'}
            </button>
          </div>
        </div>

        {features && (
          <div className="output-section">
            <h2>Audio Features</h2>
            <div className="features-grid">
              <div className="feature-item">
                <label>Duration</label>
                <p>{features.duration?.toFixed(2)} seconds</p>
              </div>
              <div className="feature-item">
                <label>Sample Rate</label>
                <p>{features.sample_rate} Hz</p>
              </div>
              <div className="feature-item">
                <label>Spectral Centroid</label>
                <p>{features.spectral_centroid?.toFixed(2)} Hz</p>
              </div>
              <div className="feature-item">
                <label>Zero Crossing Rate</label>
                <p>{features.zero_crossing_rate?.toFixed(4)}</p>
              </div>
            </div>
          </div>
        )}

        {silentSegments.length > 0 && (
          <div className="output-section">
            <h2>Silent Segments</h2>
            <div className="segments-list">
              {silentSegments.map((segment, index) => (
                <div key={index} className="segment-item">
                  <span>{segment.toFixed(2)}s</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AudioProcessor;
