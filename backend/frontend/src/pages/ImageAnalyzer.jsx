import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import './ImageAnalyzer.css';

function ImageAnalyzer() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState('');

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
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
    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post('http://localhost:5000/api/image/analyze', formData);
      setAnalysis(response.data.description);
      toast.success('Image analyzed successfully!');
    } catch (error) {
      toast.error('Error analyzing image: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="image-analyzer">
      <h1>Image Analyzer</h1>
      
      <div className="analyzer-container">
        <div className="input-section">
          <label>Select Image</label>
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
          <div className="output-section">
            <h2>Analysis Result</h2>
            <div className="analysis-box">
              {analysis}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageAnalyzer;
