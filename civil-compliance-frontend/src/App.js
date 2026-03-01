import React, { useState } from 'react';
import axios from 'axios';
import './styles/App.css';

function App() {
  const [clause, setClause] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkCompliance = async () => {
    if (!clause.trim()) {
      setError('Please enter a clause to check');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/check-compliance', {
        clause: clause
      });
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to check compliance');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Civil Compliance Auditor</h1>
        <p>Check your legal clauses against civil statutes</p>
      </header>

      <main className="App-main">
        <div className="input-section">
          <textarea
            value={clause}
            onChange={(e) => setClause(e.target.value)}
            placeholder="Enter your legal clause here..."
            rows={6}
          />
          <button onClick={checkCompliance} disabled={loading}>
            {loading ? 'Checking...' : 'Check Compliance'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {results && (
          <div className="results-section">
            <h2>Compliance Results</h2>
            <div className="results">
              {results.results?.map((result, index) => (
                <div key={index} className={`result-card ${result.label?.toLowerCase()}`}>
                  <h3>{result.statute_id}</h3>
                  <p className="statute-text">{result.statute_text}</p>
                  <div className="verdict">
                    <span className="label">{result.label}</span>
                    <span className="confidence">Confidence: {(result.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              )) || <p>No results found</p>}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
