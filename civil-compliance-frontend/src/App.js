import React, { useState } from 'react';
import UploadPage from './components/UploadPage';
import ResultPage from './components/ResultPage';
import MandatoryClausesPage from './components/MandatoryClausesPage';
import HistoryPage from './components/HistoryPage';
import './styles/App.css';

function App() {
  const [results, setResults] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [currentPage, setCurrentPage] = useState('upload'); // 'upload', 'results', 'mandatory', 'history'

  const handleResults = (data, fileName) => {
    setResults(data);
    setUploadedFileName(fileName || 'document');
    setCurrentPage('results');
  };

  const handleBack = () => {
    setCurrentPage('upload');
  };

  const handleReAnalyze = () => {
    setResults(null);
    setCurrentPage('upload');
  };

  const handleViewMandatory = () => {
    setCurrentPage('mandatory');
  };

  const handleBackToResults = () => {
    setCurrentPage('results');
  };

  const handleViewHistory = () => {
    setCurrentPage('history');
  };

  const handleViewHistoryDocument = (documentData) => {
    // Convert stored analysis result to the format expected by ResultPage
    const formattedResults = {
      domain: documentData.analysis_result?.domain,
      clauses: documentData.analysis_result?.clauses || [],
      missing_mandatory: documentData.analysis_result?.missing_mandatory || []
    };
    setResults(formattedResults);
    setUploadedFileName(documentData.file_name || 'document');
    setCurrentPage('results');
  };

  return (
    <div className="App">
      {/* Professional Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className="brand-text">
            <h1>Civil Compliance Auditor</h1>
            <span className="brand-tagline">AI-Powered Legal Document Analysis</span>
          </div>
        </div>
        <div className="navbar-actions">
          <button 
            className={`nav-link-btn ${currentPage === 'upload' ? 'active' : ''}`}
            onClick={handleBack}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span>Upload</span>
          </button>
          <button 
            className={`nav-link-btn ${currentPage === 'history' ? 'active' : ''}`}
            onClick={handleViewHistory}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <span>History</span>
          </button>
          <div className="nav-badge">
            <span className="badge-dot"></span>
            Legal-BERT NLI
          </div>
        </div>
      </nav>

      <main className="App-main">
        {currentPage === 'upload' && (
          <UploadPage onResults={handleResults} />
        )}
        {currentPage === 'results' && results && (
          <ResultPage 
            results={results} 
            onBack={handleBack}
            onReAnalyze={handleReAnalyze}
            onViewMandatory={handleViewMandatory}
          />
        )}
        {currentPage === 'mandatory' && results && (
          <MandatoryClausesPage 
            results={results}
            fileName={uploadedFileName}
            onBack={handleBackToResults}
          />
        )}
        {currentPage === 'history' && (
          <HistoryPage 
            onBack={handleBack}
            onViewDocument={handleViewHistoryDocument}
          />
        )}
      </main>

      <footer className="App-footer">
        <div className="footer-content">
          <div className="footer-left">
            <span className="footer-icon">🔒</span>
            <span>Your documents are processed securely and stored in your history</span>
          </div>
          <div className="footer-center">
            <span>Hybrid AI System: Machine Learning + Rule-Based Logic</span>
          </div>
          <div className="footer-right">
            <span>Sri Lanka Legal Framework</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
