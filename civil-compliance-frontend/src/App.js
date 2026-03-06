import React, { useState } from 'react';
import UploadPage from './components/UploadPage';
import ResultPage from './components/ResultPage';
import HistoryPage from './components/HistoryPage';
import MandatoryClausesPage from './components/MandatoryClausesPage';
import DownloadActsPage from './components/DownloadActsPage';
import './styles/App.css';

function App() {
  const [results, setResults] = useState(null);
  const [currentPage, setCurrentPage] = useState('upload');
  const [activeFilter, setActiveFilter] = useState('all');

  const handleResults = (data) => {
    setResults(data);
    setCurrentPage('results');
  };

  const handleBack = () => {
    setCurrentPage('upload');
  };

  const handleReAnalyze = () => {
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

  const handleViewMandatoryClauses = () => {
    setCurrentPage('mandatory');
  };

  const handleViewDownloadActs = () => {
    setCurrentPage('acts');
  };

  const handleFilterNavigation = (filter) => {
    setActiveFilter(filter);
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
            <span className="nav-icon">🏠</span>
            Home
          </button>
          {results && (
            <>
              <button 
                className={`nav-link ${currentPage === 'results' ? 'active' : ''}`}
                onClick={() => setCurrentPage('results')}
              >
                <span className="nav-icon">📊</span>
                Results
              </button>
              <button 
                className={`nav-link ${currentPage === 'mandatory' ? 'active' : ''}`}
                onClick={handleViewMandatoryClauses}
              >
                <span className="nav-icon">📜</span>
                Mandatory Clauses
              </button>
              <button 
                className={`nav-link ${currentPage === 'acts' ? 'active' : ''}`}
                onClick={handleViewDownloadActs}
              >
                <span className="nav-icon">📚</span>
                Download Acts
              </button>
            </>
          )}
          <button 
            className={`nav-link ${currentPage === 'history' ? 'active' : ''}`}
            onClick={handleViewHistory}
          >
            <span className="nav-icon">📋</span>
            History
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {currentPage === 'upload' && (
          <UploadPage onResults={handleResults} />
        )}
        {currentPage === 'results' && results && (
          <ResultPage 
            results={results} 
            onBack={handleReAnalyze}
            onViewMandatory={handleViewMandatoryClauses}
            onViewActs={handleViewDownloadActs}
            activeFilter={activeFilter}
            setActiveFilter={setActiveFilter}
          />
        )}
        {currentPage === 'mandatory' && results && (
          <MandatoryClausesPage 
            results={results} 
            onBack={() => setCurrentPage('results')}
            onReAnalyze={handleReAnalyze}
          />
        )}
        {currentPage === 'acts' && (
          <DownloadActsPage 
            onBack={() => results ? setCurrentPage('results') : setCurrentPage('upload')}
            onReAnalyze={handleReAnalyze}
          />
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
