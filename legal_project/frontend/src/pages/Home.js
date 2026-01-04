import React from 'react';
import './Home.css';

function Home() {
  return (
    <div className="container home-page">
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
