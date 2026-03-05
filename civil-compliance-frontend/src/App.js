import React, { useState } from 'react';
import UploadPage from './components/UploadPage';
import ResultPage from './components/ResultPage';
import HistoryPage from './components/HistoryPage';
import './styles/App.css';

function App() {
  const [results, setResults] = useState(null);
  const [currentPage, setCurrentPage] = useState('upload');

  const handleResults = (data) => {
    setResults(data);
    setCurrentPage('results');
  };

  const handleBack = () => {
    setResults(null);
    setCurrentPage('upload');
  };

  const handleViewHistory = () => {
    setCurrentPage('history');
  };

  const handleViewAnalysis = (data) => {
    setResults(data);
    setCurrentPage('results');
  };

  return (
    <div className="app">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <span className="brand-icon">⚖️</span>
          <span className="brand-text">Legal Compliance Analyzer</span>
        </div>
        <div className="navbar-links">
          <button 
            className={`nav-link ${currentPage === 'upload' ? 'active' : ''}`}
            onClick={handleBack}
          >
            Home
          </button>
          <button 
            className={`nav-link ${currentPage === 'history' ? 'active' : ''}`}
            onClick={handleViewHistory}
          >
            📋 History
          </button>
          <a href="#about" className="nav-link">About</a>
          <a href="#help" className="nav-link">Help</a>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {currentPage === 'upload' && (
          <UploadPage onResults={handleResults} />
        )}
        {currentPage === 'results' && results && (
          <ResultPage results={results} onBack={handleBack} />
        )}
        {currentPage === 'history' && (
          <HistoryPage onViewAnalysis={handleViewAnalysis} onBack={handleBack} />
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <span className="footer-icon">🔒</span>
            <span>Your documents are processed securely and stored in MongoDB</span>
          </div>
          <div className="footer-divider"></div>
          <div className="footer-section">
            <span className="footer-icon">🤖</span>
            <span>Powered by Legal-BERT NLI & Advanced AI</span>
          </div>
          <div className="footer-divider"></div>
          <div className="footer-section">
            <span className="footer-icon">📋</span>
            <span>Sri Lanka Legal Compliance Standards</span>
          </div>
        </div>
        <div className="footer-copyright">
          © 2026 Legal Compliance Analyzer. All rights reserved.
        </div>
      </footer>
    </div>
  );
}

export default App;
