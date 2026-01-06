import React, { useState, useEffect } from 'react';
import './Home.css';
import caseService from '../services/caseService';

function Home() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [statusMessage, setStatusMessage] = useState('Connecting to backend...');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await caseService.checkHealth();
        setBackendStatus('connected');
        setStatusMessage('✅ Backend Connected');
      } catch (error) {
        setBackendStatus('disconnected');
        setStatusMessage('❌ Backend Offline - Make sure server is running on http://localhost:5000');
      }
    };

    checkBackend();
  }, []);

  return (
    <div className="container home-page">
      {/* Backend Status Banner */}
      <div style={{ 
        background: backendStatus === 'connected' ? '#d4edda' : '#f8d7da',
        border: `1px solid ${backendStatus === 'connected' ? '#c3e6cb' : '#f5c6cb'}`,
        color: backendStatus === 'connected' ? '#155724' : '#721c24',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        textAlign: 'center'
      }}>
        <strong>{statusMessage}</strong>
      </div>
      <div className="intro-section">
        <h2>Welcome to Legal Case Analyzer</h2>
        <p>Intelligent legal document analysis and case classification system</p>
        <p>Upload legal PDFs, extract text, classify cases, and find similar cases with our advanced AI-powered system.</p>
      </div>

      <div className="features-grid">
        <div className="feature-card">
          <h3>📤 Upload & Extract</h3>
          <p>Upload legal PDF documents and automatically extract text using OCR technology.</p>
        </div>
        <div className="feature-card">
          <h3>🏷️ Smart Classification</h3>
          <p>Automatically classify cases into categories like Civil, Criminal, Family, Tax, and more.</p>
        </div>
        <div className="feature-card">
          <h3>🔍 Find Similar Cases</h3>
          <p>Discover similar legal cases using advanced similarity matching algorithms.</p>
        </div>
        <div className="feature-card">
          <h3>⚙️ Accurate Analysis</h3>
          <p>Get detailed analysis and predictions powered by machine learning models.</p>
        </div>
      </div>

      <div className="cta-section">
        <h3>Get Started</h3>
        <a href="/upload" className="btn btn-primary btn-lg">Upload Your First Document</a>
      </div>
    </div>
  );
}

export default Home;
