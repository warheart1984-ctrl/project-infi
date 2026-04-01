import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import './ImageGenerator.css';

function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [steps, setSteps] = useState(50);
  const [loading, setLoading] = useState(false);
  const [generatedImage, setGeneratedImage] = useState('');

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/image/generate', {
        prompt,
        num_inference_steps: steps
      });
      setGeneratedImage(`data:image/png;base64,${response.data.image}`);
      toast.success('Image generated successfully!');
    } catch (error) {
      toast.error('Error generating image: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = 'generated-image.png';
    link.click();
    toast.success('Image downloaded!');
  };

  return (
    <div className="image-generator">
      <h1>Image Generator</h1>
      
      <div className="generator-container">
        <div className="input-section">
          <label>Image Description</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to generate..."
            rows="6"
          />

          <div className="controls">
            <div className="control-group">
              <label>Inference Steps: {steps}</label>
              <input
                type="range"
                min="10"
                max="100"
                value={steps}
                onChange={(e) => setSteps(Number(e.target.value))}
              />
            </div>
          </div>

          <button
            className="generate-btn"
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate Image'}
          </button>
        </div>

        {generatedImage && (
          <div className="output-section">
            <h2>Generated Image</h2>
            <img src={generatedImage} alt="Generated" className="generated-image" />
            <button className="download-btn" onClick={handleDownload}>
              Download Image
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageGenerator;
