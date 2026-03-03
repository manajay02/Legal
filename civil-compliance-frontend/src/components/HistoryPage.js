import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/HistoryPage.css';

function HistoryPage({ onBack, onViewDocument }) {
  const [history, setHistory] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchHistory();
    fetchStatistics();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8002/history');
      setHistory(response.data.history);
      setError(null);
    } catch (err) {
      setError('Failed to load history');
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get('http://localhost:8002/statistics');
      setStatistics(response.data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  };

  const handleDelete = async (documentId) => {
    try {
      await axios.delete(`http://localhost:8002/history/${documentId}`);
      setHistory(history.filter(doc => doc._id !== documentId));
      setDeleteConfirm(null);
      fetchStatistics(); // Refresh statistics
    } catch (err) {
      setError('Failed to delete document');
      console.error('Error deleting document:', err);
    }
  };

  const handleViewDetails = async (documentId) => {
    try {
      const response = await axios.get(`http://localhost:8002/history/${documentId}`);
      onViewDocument(response.data);
    } catch (err) {
      setError('Failed to load document details');
      console.error('Error fetching document:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getComplianceColor = (percentage) => {
    if (percentage >= 80) return '#22c55e';
    if (percentage >= 60) return '#84cc16';
    if (percentage >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const getComplianceStatus = (percentage) => {
    if (percentage >= 80) return 'Excellent';
    if (percentage >= 60) return 'Good';
    if (percentage >= 40) return 'Fair';
    return 'Needs Review';
  };

  return (
    <div className="history-page">
      {/* Top Navigation */}
      <div className="history-nav">
        <button className="nav-btn back-btn" onClick={onBack}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          <span>Back to Upload</span>
        </button>
        <button className="nav-btn refresh-btn" onClick={fetchHistory}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23,4 23,10 17,10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          <span>Refresh</span>
        </button>
      </div>

      {/* Page Header */}
      <div className="history-header">
        <div className="header-content">
          <h1>
            <span className="header-icon">📜</span>
            Analysis History
          </h1>
          <p>View and manage your previously analyzed documents</p>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="statistics-section">
          <h2 className="section-title">
            <span className="title-icon">📊</span>
            Your Statistics
          </h2>
          <div className="statistics-cards">
            <div className="stat-card">
              <div className="stat-icon documents">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                </svg>
              </div>
              <div className="stat-content">
                <span className="stat-value">{statistics.total_documents}</span>
                <span className="stat-label">Documents Analyzed</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon compliance">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <div className="stat-content">
                <span className="stat-value">{statistics.avg_compliance}%</span>
                <span className="stat-label">Avg. Compliance</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon clauses">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="8" y1="6" x2="21" y2="6"/>
                  <line x1="8" y1="12" x2="21" y2="12"/>
                  <line x1="8" y1="18" x2="21" y2="18"/>
                  <line x1="3" y1="6" x2="3.01" y2="6"/>
                  <line x1="3" y1="12" x2="3.01" y2="12"/>
                  <line x1="3" y1="18" x2="3.01" y2="18"/>
                </svg>
              </div>
              <div className="stat-content">
                <span className="stat-value">{statistics.total_clauses_analyzed}</span>
                <span className="stat-label">Clauses Analyzed</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon compliant">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="16 12 12 8 8 12"/>
                  <line x1="12" y1="16" x2="12" y2="8"/>
                </svg>
              </div>
              <div className="stat-content">
                <span className="stat-value">{statistics.total_compliant}</span>
                <span className="stat-label">Compliant Clauses</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon violations">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
              </div>
              <div className="stat-content">
                <span className="stat-value">{statistics.total_violations}</span>
                <span className="stat-label">Violations Found</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History List */}
      <div className="history-list-section">
        <h2 className="section-title">
          <span className="title-icon">📁</span>
          Document History
          <span className="count-badge">{history.length}</span>
        </h2>

        {loading && (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading history...</p>
          </div>
        )}

        {error && (
          <div className="error-state">
            <span className="error-icon">⚠️</span>
            <p>{error}</p>
            <button onClick={fetchHistory}>Try Again</button>
          </div>
        )}

        {!loading && !error && history.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No Documents Yet</h3>
            <p>Upload and analyze documents to see them here</p>
            <button className="empty-action-btn" onClick={onBack}>
              Upload Document
            </button>
          </div>
        )}

        {!loading && !error && history.length > 0 && (
          <div className="history-table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Domain</th>
                  <th>Compliance</th>
                  <th>Clauses</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((doc) => (
                  <tr key={doc._id}>
                    <td className="document-cell">
                      <div className="document-info">
                        <span className="file-icon">
                          {doc.file_type === 'pdf' ? '📄' : '📝'}
                        </span>
                        <div className="file-details">
                          <span className="file-name">{doc.file_name}</span>
                          <span className="file-type">{doc.file_type?.toUpperCase()}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="domain-badge">
                        {doc.analysis_result?.domain?.toUpperCase() || 'GENERAL'}
                      </span>
                    </td>
                    <td>
                      <div className="compliance-indicator">
                        <div 
                          className="compliance-bar"
                          style={{ 
                            '--compliance': `${doc.compliance_percentage || 0}%`,
                            '--compliance-color': getComplianceColor(doc.compliance_percentage || 0)
                          }}
                        >
                          <div className="compliance-fill"></div>
                        </div>
                        <span 
                          className="compliance-text"
                          style={{ color: getComplianceColor(doc.compliance_percentage || 0) }}
                        >
                          {doc.compliance_percentage || 0}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="clauses-info">
                        <span className="compliant-count">
                          ✅ {doc.analysis_result?.compliant_count || 0}
                        </span>
                        <span className="violation-count">
                          ❌ {doc.analysis_result?.violation_count || 0}
                        </span>
                      </div>
                    </td>
                    <td className="date-cell">
                      {formatDate(doc.uploaded_at)}
                    </td>
                    <td className="actions-cell">
                      <button 
                        className="action-btn view-btn"
                        onClick={() => handleViewDetails(doc._id)}
                        title="View Details"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      </button>
                      <button 
                        className="action-btn delete-btn"
                        onClick={() => setDeleteConfirm(doc._id)}
                        title="Delete"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3,6 5,6 21,6"/>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                          <line x1="10" y1="11" x2="10" y2="17"/>
                          <line x1="14" y1="11" x2="14" y2="17"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-icon">⚠️</span>
              <h3>Delete Document</h3>
            </div>
            <p>Are you sure you want to delete this document from your history? This action cannot be undone.</p>
            <div className="modal-actions">
              <button 
                className="modal-btn cancel-btn"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
              <button 
                className="modal-btn confirm-btn"
                onClick={() => handleDelete(deleteConfirm)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HistoryPage;
