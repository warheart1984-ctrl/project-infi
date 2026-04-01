import React from 'react';
import { Link } from 'react-router-dom';
import { FiArrowRight } from 'react-icons/fi';
import './Dashboard.css';

function Dashboard() {
  const features = [
    {
      title: 'Text Generator',
      description: 'Generate uncensored text on any topic',
      path: '/text-generator',
      icon: '📝'
    },
    {
      title: 'Image Analyzer',
      description: 'Analyze and describe images in detail',
      path: '/image-analyzer',
      icon: '🔍'
    },
    {
      title: 'Image Generator',
      description: 'Create images from text descriptions',
      path: '/image-generator',
      icon: '🎨'
    },
    {
      title: 'Audio Processor',
      description: 'Extract features and analyze audio',
      path: '/audio-processor',
      icon: '🎵'
    },
    {
      title: 'Batch Processor',
      description: 'Process multiple items in parallel',
      path: '/batch-processor',
      icon: '⚡'
    },
    {
      title: 'History',
      description: 'View your generation history',
      path: '/history',
      icon: '📚'
    }
  ];

  return (
    <div className="dashboard">
      <div className="hero">
        <h1>Welcome to AAIS</h1>
        <p>Uncensored Multi-Modal AI System</p>
      </div>

      <div className="features-grid">
        {features.map((feature, index) => (
          <Link key={index} to={feature.path} className="feature-card">
            <div className="feature-icon">{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
            <div className="feature-arrow">
              <FiArrowRight />
            </div>
          </Link>
        ))}
      </div>

      <div className="stats">
        <div className="stat-card">
          <h3>0</h3>
          <p>Texts Generated</p>
        </div>
        <div className="stat-card">
          <h3>0</h3>
          <p>Images Generated</p>
        </div>
        <div className="stat-card">
          <h3>0</h3>
          <p>Audio Processed</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
