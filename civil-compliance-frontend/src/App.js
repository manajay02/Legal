import React, { useState } from 'react';
import UploadPage from './components/UploadPage';
import ResultPage from './components/ResultPage';
import './styles/App.css';

function App() {
  const [results, setResults] = useState(null);
  const [currentPage, setCurrentPage] = useState('upload'); // 'upload' or 'results'

  const handleResults = (data) => {
    setResults(data);
    setCurrentPage('results');
  };

  const handleBack = () => {
    setResults(null);
    setCurrentPage('upload');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Civil Compliance Auditor</h1>
        <p>AI-Powered Legal Document Analysis using Legal-BERT NLI</p>
      </header>

      <main className="App-main">
        {currentPage === 'upload' && (
          <UploadPage onResults={handleResults} />
        )}
        {currentPage === 'results' && results && (
          <ResultPage results={results} onBack={handleBack} />
        )}
      </main>

      <footer className="App-footer">
        <p>Hybrid AI System: Machine Learning + Rule-Based Logic</p>
      </footer>
    </div>
  );
}

export default App;
