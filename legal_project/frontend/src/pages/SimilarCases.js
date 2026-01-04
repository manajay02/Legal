import React, { useState } from 'react';
import './SimilarCases.css';

function SimilarCases() {
  const [caseFile, setCaseFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('upload'); // upload, processing, results
  const [selectedCase, setSelectedCase] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (e) => {
    setCaseFile(e.target.files[0]);
  };

  const analyzeSimilarCases = async () => {
    if (!caseFile) {
      alert('Please select a case file');
      return;
    }

    setLoading(true);
    setStep('processing');
    setUploadProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 30;
      });
    }, 300);

    // Simulated API call with your trained model
    setTimeout(() => {
      clearInterval(progressInterval);
      setUploadProgress(100);

      const similarCases = [
        {
          id: '2023-045',
          title: 'Smith v. Johnson - Contract Breach',
          similarity: 92,
          court: 'District Court',
          year: 2023,
          category: 'Civil Contract Dispute',
          outcome: 'Settled',
          relevantPoints: [
            'Similar breach of warranty clause',
            'Comparable damages calculation',
            'Same jurisdiction and court'
          ]
        },
        {
          id: '2022-187',
          title: 'ABC Corp v. XYZ Industries - Service Agreement',
          similarity: 87,
          court: 'Appeals Court',
          year: 2022,
          category: 'Commercial Dispute',
          outcome: 'Plaintiff Won',
          relevantPoints: [
            'Similar contractual obligations',
            'Comparable party dynamics',
            'Related industry standards'
          ]
        },
        {
          id: '2023-012',
          title: 'Davis & Co. v. Turner LLC - Liability Case',
          similarity: 79,
          court: 'District Court',
          year: 2023,
          category: 'Civil Liability',
          outcome: 'Settled',
          relevantPoints: [
            'Similar liability arguments',
            'Comparable negligence claims',
            'Relevant precedent'
          ]
        },
        {
          id: '2021-256',
          title: 'Green v. Williams - Insurance Claim',
          similarity: 76,
          court: 'Superior Court',
          year: 2021,
          category: 'Insurance Dispute',
          outcome: 'Plaintiff Won',
          relevantPoints: [
            'Similar claim structure',
            'Comparable insurance interpretation',
            'Related coverage issues'
          ]
        },
        {
          id: '2023-033',
          title: 'Martinez Corporation v. Anderson - Trade Dispute',
          similarity: 71,
          court: 'District Court',
          year: 2023,
          category: 'Commercial Trade',
          outcome: 'Defendant Won',
          relevantPoints: [
            'Related trade practices',
            'Comparable market conditions',
            'Similar legal frameworks'
          ]
        }
      ];

      setResults(similarCases);
      setStep('results');
      setLoading(false);
    }, 2000);
  };

  const viewCaseDetails = (caseItem) => {
    setSelectedCase(caseItem);
  };

  const closeCaseDetails = () => {
    setSelectedCase(null);
  };

  const resetWorkflow = () => {
    setCaseFile(null);
    setResults([]);
    setStep('upload');
    setUploadProgress(0);
    setSelectedCase(null);
  };

  return (
    <div className="container">
      <h2>⚖️ Similar Cases Analyzer</h2>

      {/* Workflow Progress */}
      <div className="workflow-progress">
        <div className={`progress-step ${step === 'upload' ? 'active' : step !== 'upload' ? 'completed' : ''}`}>
          <div className="step-number">1</div>
          <p>Upload</p>
        </div>
        <div className="progress-line"></div>
        <div className={`progress-step ${step === 'processing' ? 'active' : step === 'results' ? 'completed' : ''}`}>
          <div className="step-number">2</div>
          <p>Processing</p>
        </div>
        <div className="progress-line"></div>
        <div className={`progress-step ${step === 'results' ? 'active completed' : ''}`}>
          <div className="step-number">3</div>
          <p>Results</p>
        </div>
      </div>

      {/* Upload Step */}
      {step === 'upload' && (
        <div className="card">
          <div className="step-header">
            <h3>📤 Step 1: Upload Your Case Document</h3>
            <p>Upload a legal case document to find similar cases from our trained model database</p>
          </div>

          <div className="upload-section">
            <div className="upload-area">
              <input
                type="file"
                id="caseFile"
                onChange={handleFileChange}
                accept=".pdf,.txt,.doc,.docx"
                className="file-input"
              />
              <label htmlFor="caseFile" className="upload-label">
                <div className="upload-icon">📁</div>
                <h4>Select or Drag Case File</h4>
                <p>Supported formats: PDF, TXT, DOC, DOCX</p>
                {caseFile && <p className="file-name">✓ {caseFile.name}</p>}
              </label>
            </div>
          </div>

          <button
            onClick={analyzeSimilarCases}
            disabled={loading || !caseFile}
            className="btn btn-primary btn-large"
          >
            {loading ? 'Processing...' : 'Analyze with AI Model'}
          </button>

          <div className="info-box">
            <h4>💡 How It Works</h4>
            <ul>
              <li>Our trained ML model analyzes your case document</li>
              <li>Extracts key legal concepts and case elements</li>
              <li>Searches database for similar cases</li>
              <li>Returns matches ranked by similarity score</li>
            </ul>
          </div>
        </div>
      )}

      {/* Processing Step */}
      {step === 'processing' && (
        <div className="card">
          <div className="step-header">
            <h3>⚙️ Step 2: AI Model Processing</h3>
            <p>Analyzing your case with our trained model...</p>
          </div>

          <div className="processing-container">
            <div className="processing-stages">
              <div className="stage processing">
                <div className="stage-icon">📖</div>
                <p>Reading Document</p>
              </div>
              <div className="stage processing">
                <div className="stage-icon">🔍</div>
                <p>Extracting Features</p>
              </div>
              <div className="stage processing">
                <div className="stage-icon">🤖</div>
                <p>Running ML Model</p>
              </div>
              <div className="stage processing">
                <div className="stage-icon">🔗</div>
                <p>Finding Matches</p>
              </div>
            </div>

            <div className="progress-bar-large">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
            </div>
            <p className="progress-text">{Math.round(uploadProgress)}% Complete</p>

            <div className="processing-info">
              <p>📄 File: <strong>{caseFile?.name}</strong></p>
              <p>🤖 Model: Legal Case Similarity Analyzer v1.0</p>
              <p>⚡ Processing time: ~2 seconds</p>
            </div>
          </div>
        </div>
      )}

      {/* Results Step */}
      {step === 'results' && (
        <div className="card">
          <div className="step-header">
            <h3>📊 Step 3: Analysis Results</h3>
            <p>Found {results.length} similar cases ranked by relevance</p>
          </div>

          <div className="results-summary">
            <div className="summary-stat">
              <h4>{results.length}</h4>
              <p>Similar Cases Found</p>
            </div>
            <div className="summary-stat">
              <h4>{Math.round(results[0]?.similarity || 0)}%</h4>
              <p>Highest Match</p>
            </div>
            <div className="summary-stat">
              <h4>{Math.round(results.reduce((sum, r) => sum + r.similarity, 0) / results.length)}%</h4>
              <p>Average Match</p>
            </div>
          </div>

          <div className="results-section">
            <h4>Similar Cases Ranked by Similarity Score</h4>
            <div className="results-list">
              {results.map((result, index) => (
                <div key={index} className="result-card">
                  <div className="result-rank">#{index + 1}</div>
                  <div className="result-main">
                    <div className="result-header">
                      <div className="result-info">
                        <h5>{result.title}</h5>
                        <div className="result-meta">
                          <span className="badge court">{result.court}</span>
                          <span className="badge year">{result.year}</span>
                          <span className="badge outcome">{result.outcome}</span>
                        </div>
                      </div>
                      <div className="similarity-score-large">
                        <span className="score">{result.similarity}%</span>
                        <span className="label">Match</span>
                      </div>
                    </div>

                    <div className="progress-bar-small">
                      <div className="progress-fill" style={{ width: `${result.similarity}%` }}></div>
                    </div>

                    <p className="category">📁 {result.category}</p>

                    <div className="relevant-points">
                      <h6>Key Relevance Points:</h6>
                      <ul>
                        {result.relevantPoints.map((point, i) => (
                          <li key={i}>{point}</li>
                        ))}
                      </ul>
                    </div>

                    <button
                      className="btn btn-secondary btn-small"
                      onClick={() => viewCaseDetails(result)}
                    >
                      View Full Details →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button className="btn btn-primary btn-block" onClick={resetWorkflow}>
            ← Analyze Another Case
          </button>
        </div>
      )}

      {/* Case Details Modal */}
      {selectedCase && (
        <div className="modal-overlay" onClick={closeCaseDetails}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeCaseDetails}>×</button>

            <div className="modal-header">
              <h3>{selectedCase.title}</h3>
              <div className="modal-badges">
                <span className="badge court">{selectedCase.court}</span>
                <span className="badge year">{selectedCase.year}</span>
                <span className="badge outcome">{selectedCase.outcome}</span>
              </div>
            </div>

            <div className="modal-body">
              <div className="modal-section">
                <h4>Case ID</h4>
                <p>{selectedCase.id}</p>
              </div>

              <div className="modal-section">
                <h4>Category</h4>
                <p>{selectedCase.category}</p>
              </div>

              <div className="modal-section">
                <h4>Similarity Score</h4>
                <div className="score-container">
                  <div className="score-bar">
                    <div className="score-fill" style={{ width: `${selectedCase.similarity}%` }}></div>
                  </div>
                  <span className="score-value">{selectedCase.similarity}% Match</span>
                </div>
              </div>

              <div className="modal-section">
                <h4>Relevant Points</h4>
                <ul className="relevant-list">
                  {selectedCase.relevantPoints.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>

              <div className="modal-section">
                <h4>Case Outcome</h4>
                <p className="outcome-text">{selectedCase.outcome}</p>
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn btn-primary" onClick={closeCaseDetails}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SimilarCases;
