import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import TextGenerator from './pages/TextGenerator';
import ImageAnalyzer from './pages/ImageAnalyzer';
import ImageGenerator from './pages/ImageGenerator';
import AudioProcessor from './pages/AudioProcessor';
import BatchProcessor from './pages/BatchProcessor';
import History from './pages/History';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/text-generator" element={<TextGenerator />} />
            <Route path="/image-analyzer" element={<ImageAnalyzer />} />
            <Route path="/image-generator" element={<ImageGenerator />} />
            <Route path="/audio-processor" element={<AudioProcessor />} />
            <Route path="/batch-processor" element={<BatchProcessor />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
