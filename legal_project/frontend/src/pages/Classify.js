import React, { useState } from 'react';
import caseService from '../services/caseService';
import './Classify.css';

function Classify() {
  const [caseText, setCaseText] = useState('');
  const [prediction, setPrediction] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleClassify = async () => {
    if (!caseText.trim()) {
      setError('Please enter case text');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await caseService.classifyCase({ text: caseText });
      setPrediction(response.data.category);
      setConfidence(response.data.confidence);
    } catch (err) {
      setError('Error classifying case: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container classify-page">
      <h2>Case Classification</h2>

      <div className="classify-card">
        <div className="input-section">
          <h3>Enter Case Text</h3>
          <textarea
            value={caseText}
            onChange={(e) => setCaseText(e.target.value)}
            placeholder="Paste the case text here..."
            className="case-textarea"
          />
          <button
            onClick={handleClassify}
            disabled={loading}
            className="btn btn-primary btn-classify"
          >
            {loading ? 'Classifying...' : 'Classify Case'}
          </button>
          {error && <div className="error-message">{error}</div>}
        </div>

        {prediction && (
          <div className="result-section">
            <h3>🎯 Classification Result</h3>
            <div className="result-box">
              <div className="result-item">
                <label>Predicted Category:</label>
                <span className="category-badge">{prediction}</span>
              </div>
              <div className="result-item">
                <label>Confidence:</label>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill" 
                    style={{ width: `${confidence * 100}%` }}
                  />
                </div>
                <span className="confidence-text">{(confidence * 100).toFixed(2)}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Classify;
