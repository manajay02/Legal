import React from 'react';
import '../styles/ResultPage.css';

function ResultPage({ results, onBack }) {
  const { domain, clauses, missing_mandatory } = results;

  const compliantClauses = clauses?.filter(c => c.status === '🟢 Compliant') || [];
  const violatedClauses = clauses?.filter(c => c.status === '🔴 Violation') || [];

  return (
    <div className="result-page">
      <button className="back-btn" onClick={onBack}>
        ← Back to Upload
      </button>

      {/* Summary Section */}
      <div className="summary-section">
        <h2>Compliance Report Summary</h2>
        <div className="summary-cards">
          <div className="summary-card domain">
            <span className="label">Detected Domain</span>
            <span className="value">{domain?.toUpperCase() || 'N/A'}</span>
          </div>
          <div className="summary-card total">
            <span className="label">Total Clauses</span>
            <span className="value">{clauses?.length || 0}</span>
          </div>
          <div className="summary-card compliant">
            <span className="label">Compliant</span>
            <span className="value">{compliantClauses.length}</span>
          </div>
          <div className="summary-card violations">
            <span className="label">Violations</span>
            <span className="value">{violatedClauses.length}</span>
          </div>
          <div className="summary-card missing">
            <span className="label">Missing</span>
            <span className="value">{missing_mandatory?.length || 0}</span>
          </div>
        </div>
      </div>

      {/* Missing Mandatory Clauses */}
      {missing_mandatory && missing_mandatory.length > 0 ? (
        <div className="missing-section">
          <h3>⚠️ Missing Mandatory Clauses</h3>
          <div className="missing-list">
            {missing_mandatory.map((item, index) => (
              <div key={index} className="missing-card">
                <div className="missing-name">{item.clause}</div>
                <div className="missing-rule">{item.rule}</div>
                <div className="missing-confidence">
                  Confidence: {item.confidence?.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="no-missing-section">
          <h3>✅ No Missing Mandatory Clauses</h3>
          <p>All required clauses are present in the document.</p>
        </div>
      )}

      {/* Violations Section */}
      {violatedClauses.length > 0 && (
        <div className="clauses-section violations-section">
          <h3>🔴 Violations Found</h3>
          <div className="clause-list">
            {violatedClauses.map((clause, index) => (
              <div key={index} className="clause-card violation">
                <div className="clause-text">{clause.clause}</div>
                <div className="clause-details">
                  <span className="violated-act">
                    <strong>Violated Act:</strong> {clause.violated_act || 'N/A'}
                  </span>
                  <span className="section">
                    <strong>Section:</strong> {clause.section || 'N/A'}
                  </span>
                  {clause.confidence && (
                    <span className="confidence">
                      <strong>Confidence:</strong> {clause.confidence.toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliant Section */}
      {compliantClauses.length > 0 && (
        <div className="clauses-section compliant-section">
          <h3>🟢 Compliant Clauses</h3>
          <div className="clause-list">
            {compliantClauses.map((clause, index) => (
              <div key={index} className="clause-card compliant">
                <div className="clause-text">{clause.clause}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Clauses Found */}
      {(!clauses || clauses.length === 0) && (
        <div className="no-results">
          <p>No clauses were extracted from the document.</p>
        </div>
      )}
    </div>
  );
}

export default ResultPage;
