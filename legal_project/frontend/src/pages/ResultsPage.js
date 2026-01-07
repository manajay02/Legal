import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import CaseCard from '../components/CaseCard';
import axios from 'axios';

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [similarCases, setSimilarCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const storedData = location.state?.caseData || JSON.parse(localStorage.getItem('uploadedCase'));
    if (storedData) {
      setCaseData(storedData);
      fetchSimilarCases(storedData.extracted_text, storedData.case_type);
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const fetchSimilarCases = async (caseText, caseType) => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/cases/find-similar', {
        case_text: caseText,
        case_type: caseType || '',
      });
      setSimilarCases(response.data.similar_cases || []);
    } catch (err) {
      setError('Failed to fetch similar cases');
      console.error('Error fetching similar cases:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!caseData) {
    return (
      <div className="container mt-5">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="container mt-4">
        <button
          className="btn btn-secondary mb-3"
          onClick={() => {
            localStorage.removeItem('uploadedCase');
            navigate('/');
          }}
        >
          ← Upload Another Document
        </button>

        <div className="row mb-4">
          <div className="col-lg-8">
            <div style={{
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <h3>📄 Uploaded Document</h3>
              <p className="mb-2">
                <strong>Classification:</strong> <span className="badge bg-success">{caseData.case_type}</span>
              </p>
              <p className="mb-2">
                <strong>Confidence:</strong> {Math.round(caseData.confidence * 100)}%
              </p>
              <p style={{ fontSize: '0.95rem', color: '#555', lineHeight: '1.6' }}>
                <strong>Preview:</strong>
              </p>
              <div style={{
                background: '#f9f9f9',
                padding: '15px',
                borderRadius: '5px',
                maxHeight: '200px',
                overflowY: 'auto',
                fontSize: '0.9rem'
              }}>
                {caseData.extracted_text?.substring(0, 500)}...
              </div>
            </div>
          </div>

          <div className="col-lg-4">
            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              padding: '20px',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <h5>✅ Legal Document Verified</h5>
              <p style={{ fontSize: '2rem', margin: '10px 0' }}>
                {Math.round(caseData.confidence * 100)}%
              </p>
              <small>Confidence Score</small>
            </div>
          </div>
        </div>

        <div>
          <h3 className="mb-4">🔍 Similar Cases Library</h3>
          {error && <div className="alert alert-danger">{error}</div>}

          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
            </div>
          ) : similarCases.length > 0 ? (
            <div>
              <p className="text-muted mb-3">
                Found <strong>{similarCases.length}</strong> similar legal cases
              </p>
              {similarCases.map((caseItem, idx) => (
                <CaseCard
                  key={idx}
                  case_name={caseItem.case_name}
                  similarity_score={caseItem.similarity_score}
                  case_type={caseItem.case_type}
                />
              ))}
            </div>
          ) : (
            <div className="alert alert-info" role="alert">
              No similar cases found in the database.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResultsPage;
