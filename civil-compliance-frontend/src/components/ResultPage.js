import React, { useState } from 'react';
import '../styles/ResultPage.css';

function ResultPage({ results, onBack, onReAnalyze, onViewMandatory }) {
  const { domain, clauses, missing_mandatory } = results;
  const [activeFilter, setActiveFilter] = useState('all'); // 'all', 'compliant', 'violations', 'missing'

  const compliantClauses = clauses?.filter(c => c.status === '🟢 Compliant') || [];
  const violatedClauses = clauses?.filter(c => c.status === '🔴 Violation') || [];
  const totalClauses = clauses?.length || 0;
  const missingCount = missing_mandatory?.length || 0;

  // Calculate compliance percentage
  const compliancePercentage = totalClauses > 0 
    ? Math.round((compliantClauses.length / totalClauses) * 100) 
    : 0;

  const getComplianceStatus = () => {
    if (compliancePercentage >= 80 && missingCount === 0) return { label: 'Excellent', color: '#22c55e', icon: '✅' };
    if (compliancePercentage >= 60) return { label: 'Good', color: '#84cc16', icon: '👍' };
    if (compliancePercentage >= 40) return { label: 'Fair', color: '#f59e0b', icon: '⚠️' };
    return { label: 'Needs Review', color: '#ef4444', icon: '❌' };
  };

  const complianceStatus = getComplianceStatus();

  const getFilteredContent = () => {
    switch (activeFilter) {
      case 'compliant':
        return { clauses: compliantClauses, showMissing: false };
      case 'violations':
        return { clauses: violatedClauses, showMissing: false };
      case 'missing':
        return { clauses: [], showMissing: true };
      default:
        return { clauses: clauses || [], showMissing: true };
    }
  };

  const filteredContent = getFilteredContent();

  const renderConfidenceBar = (confidence) => {
    const percentage = confidence || 0;
    let barColor = '#ef4444';
    if (percentage >= 80) barColor = '#22c55e';
    else if (percentage >= 60) barColor = '#84cc16';
    else if (percentage >= 40) barColor = '#f59e0b';

    return (
      <div className="confidence-bar-container">
        <div className="confidence-bar">
          <div 
            className="confidence-fill" 
            style={{ width: `${percentage}%`, backgroundColor: barColor }}
          />
        </div>
        <span className="confidence-value">{percentage.toFixed(1)}%</span>
      </div>
    );
  };

  return (
    <div className="result-page">
      {/* Top Navigation */}
      <div className="result-nav">
        <button className="nav-btn back-btn" onClick={onBack}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          <span>Back to Upload</span>
        </button>
        <div className="nav-actions">
          <button className="nav-btn action-btn" onClick={onViewMandatory}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <span>View Mandatory Clauses</span>
          </button>
          <button className="nav-btn action-btn primary" onClick={onReAnalyze}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23,4 23,10 17,10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            <span>Re-analyze</span>
          </button>
        </div>
      </div>

      {/* Report Header */}
      <div className="report-header">
        <div className="report-title">
          <h1>Compliance Analysis Report</h1>
          <div className="domain-badge">
            <span className="domain-icon">📋</span>
            <span className="domain-text">{domain?.toUpperCase() || 'GENERAL'} CONTRACT</span>
          </div>
        </div>
        <div className="compliance-score">
          <div className="score-circle" style={{ '--score-color': complianceStatus.color }}>
            <svg viewBox="0 0 36 36" className="score-chart">
              <path
                className="score-bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="score-fill"
                strokeDasharray={`${compliancePercentage}, 100`}
                style={{ stroke: complianceStatus.color }}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="score-value">
              <span className="percentage">{compliancePercentage}%</span>
              <span className="label">Compliant</span>
            </div>
          </div>
          <div className="score-status" style={{ color: complianceStatus.color }}>
            <span className="status-icon">{complianceStatus.icon}</span>
            <span className="status-label">{complianceStatus.label}</span>
          </div>
        </div>
      </div>

      {/* Summary Stats - Clickable */}
      <div className="summary-section">
        <h2 className="section-title">
          <span className="title-icon">📊</span>
          Summary Statistics
          <span className="title-hint">(Click to filter)</span>
        </h2>
        <div className="summary-cards">
          <div 
            className={`summary-card total ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            <div className="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
              </svg>
            </div>
            <div className="card-content">
              <span className="card-value">{totalClauses}</span>
              <span className="card-label">Total Clauses</span>
            </div>
            <div className="card-indicator"></div>
          </div>

          <div 
            className={`summary-card compliant ${activeFilter === 'compliant' ? 'active' : ''}`}
            onClick={() => setActiveFilter('compliant')}
          >
            <div className="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22,4 12,14.01 9,11.01"/>
              </svg>
            </div>
            <div className="card-content">
              <span className="card-value">{compliantClauses.length}</span>
              <span className="card-label">Compliant</span>
            </div>
            <div className="card-indicator"></div>
          </div>

          <div 
            className={`summary-card violations ${activeFilter === 'violations' ? 'active' : ''}`}
            onClick={() => setActiveFilter('violations')}
          >
            <div className="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            </div>
            <div className="card-content">
              <span className="card-value">{violatedClauses.length}</span>
              <span className="card-label">Violations</span>
            </div>
            <div className="card-indicator"></div>
          </div>

          <div 
            className={`summary-card missing ${activeFilter === 'missing' ? 'active' : ''}`}
            onClick={() => setActiveFilter('missing')}
          >
            <div className="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <div className="card-content">
              <span className="card-value">{missingCount}</span>
              <span className="card-label">Missing</span>
            </div>
            <div className="card-indicator"></div>
          </div>
        </div>
      </div>

      {/* Active Filter Indicator */}
      {activeFilter !== 'all' && (
        <div className="filter-indicator">
          <span>Showing: <strong>{activeFilter === 'compliant' ? 'Compliant Clauses' : activeFilter === 'violations' ? 'Violations' : 'Missing Clauses'}</strong></span>
          <button className="clear-filter" onClick={() => setActiveFilter('all')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
            Clear Filter
          </button>
        </div>
      )}

      {/* Missing Mandatory Clauses */}
      {(activeFilter === 'all' || activeFilter === 'missing') && filteredContent.showMissing && (
        <>
          {missing_mandatory && missing_mandatory.length > 0 ? (
            <div className="clauses-section missing-section">
              <h3 className="section-title">
                <span className="title-icon warning">⚠️</span>
                Missing Mandatory Clauses
                <span className="count-badge missing">{missing_mandatory.length}</span>
              </h3>
              <div className="clause-grid">
                {missing_mandatory.map((item, index) => (
                  <div key={index} className="clause-card missing">
                    <div className="clause-header">
                      <span className="clause-status-icon">❌</span>
                      <h4 className="clause-name">{item.clause}</h4>
                    </div>
                    <div className="clause-body">
                      <div className="clause-rule">
                        <span className="rule-label">Required by:</span>
                        <span className="rule-text">{item.rule}</span>
                      </div>
                      <div className="clause-confidence">
                        <span className="confidence-label">Detection Confidence</span>
                        {renderConfidenceBar(item.confidence)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : activeFilter === 'all' && (
            <div className="success-banner">
              <div className="banner-icon">✅</div>
              <div className="banner-content">
                <h3>All Mandatory Clauses Present</h3>
                <p>Your document contains all required mandatory clauses for this contract type.</p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Violations Section */}
      {(activeFilter === 'all' || activeFilter === 'violations') && violatedClauses.length > 0 && (
        <div className="clauses-section violations-section">
          <h3 className="section-title">
            <span className="title-icon danger">🔴</span>
            Violations Found
            <span className="count-badge violations">{violatedClauses.length}</span>
          </h3>
          <div className="clause-list">
            {violatedClauses.map((clause, index) => (
              <div key={index} className="clause-card violation">
                <div className="clause-header">
                  <span className="clause-status-icon">❌</span>
                  <div className="clause-status-badge violation">Violation</div>
                </div>
                <div className="clause-body">
                  <div className="clause-text">
                    <span className="text-label">Clause Text:</span>
                    <p>{clause.clause}</p>
                  </div>
                  <div className="clause-details">
                    <div className="detail-item">
                      <span className="detail-icon">⚖️</span>
                      <div className="detail-content">
                        <span className="detail-label">Violated Act</span>
                        <span className="detail-value">{clause.violated_act || 'N/A'}</span>
                      </div>
                    </div>
                    <div className="detail-item">
                      <span className="detail-icon">📑</span>
                      <div className="detail-content">
                        <span className="detail-label">Section</span>
                        <span className="detail-value">{clause.section || 'N/A'}</span>
                      </div>
                    </div>
                    <div className="detail-item">
                      <span className="detail-icon">📖</span>
                      <div className="detail-content">
                        <span className="detail-label">Correct Rule</span>
                        <span className="detail-value">{clause.correct_rule || clause.rule || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                  {clause.confidence && (
                    <div className="clause-confidence">
                      <span className="confidence-label">Match Confidence</span>
                      {renderConfidenceBar(clause.confidence)}
                    </div>
                  )}
                  {clause.explanation && (
                    <div className="clause-explanation">
                      <span className="explanation-label">Explanation:</span>
                      <p>{clause.explanation}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliant Section */}
      {(activeFilter === 'all' || activeFilter === 'compliant') && compliantClauses.length > 0 && (
        <div className="clauses-section compliant-section">
          <h3 className="section-title">
            <span className="title-icon success">🟢</span>
            Compliant Clauses
            <span className="count-badge compliant">{compliantClauses.length}</span>
          </h3>
          <div className="clause-list">
            {compliantClauses.map((clause, index) => (
              <div key={index} className="clause-card compliant">
                <div className="clause-header">
                  <span className="clause-status-icon">✅</span>
                  <div className="clause-status-badge compliant">Compliant</div>
                </div>
                <div className="clause-body">
                  <div className="clause-text">
                    <span className="text-label">Clause Text:</span>
                    <p>{clause.clause}</p>
                  </div>
                  {clause.matched_rule && (
                    <div className="clause-details compact">
                      <div className="detail-item">
                        <span className="detail-icon">✓</span>
                        <div className="detail-content">
                          <span className="detail-label">Matched Rule</span>
                          <span className="detail-value">{clause.matched_rule}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {clause.confidence && (
                    <div className="clause-confidence">
                      <span className="confidence-label">Match Confidence</span>
                      {renderConfidenceBar(clause.confidence)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results Fallback */}
      {(!clauses || clauses.length === 0) && !missing_mandatory?.length && (
        <div className="no-results">
          <div className="no-results-icon">📄</div>
          <h3>No Clauses Extracted</h3>
          <p>We couldn't extract any clauses from your document. Please try uploading a different document or check the format.</p>
          <button className="retry-btn" onClick={onReAnalyze}>
            Try Again
          </button>
        </div>
      )}

      {/* Empty Filter State */}
      {activeFilter === 'violations' && violatedClauses.length === 0 && (
        <div className="empty-filter-state success">
          <div className="state-icon">🎉</div>
          <h3>No Violations Found!</h3>
          <p>Great news! Your document doesn't have any compliance violations.</p>
        </div>
      )}

      {activeFilter === 'compliant' && compliantClauses.length === 0 && (
        <div className="empty-filter-state warning">
          <div className="state-icon">⚠️</div>
          <h3>No Compliant Clauses</h3>
          <p>None of the analyzed clauses were found to be compliant.</p>
        </div>
      )}

      {activeFilter === 'missing' && (!missing_mandatory || missing_mandatory.length === 0) && (
        <div className="empty-filter-state success">
          <div className="state-icon">✅</div>
          <h3>All Required Clauses Present</h3>
          <p>Your document contains all mandatory clauses for this contract type.</p>
        </div>
      )}
    </div>
  );
}

export default ResultPage;
