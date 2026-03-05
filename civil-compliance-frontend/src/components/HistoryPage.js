import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/HistoryPage.css';

function HistoryPage({ onViewAnalysis, onBack }) {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalAnalyses, setTotalAnalyses] = useState(0);
  const [deletingId, setDeletingId] = useState(null);
  const itemsPerPage = 10;

  const documentIcons = {
    employment: '👔',
    rental: '🏠',
    sales: '📦',
    service: '🛠️',
    nda: '🔒',
    finance_leasing: '🚗',
    consumer: '💰',
    partnership: '🤝',
    general: '📄',
    other: '📄',
    unknown: '📄'
  };

  useEffect(() => {
    fetchHistory();
  }, [currentPage]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (currentPage - 1) * itemsPerPage;
      const response = await axios.get(`http://localhost:8002/history?limit=${itemsPerPage}&skip=${skip}`);
      setAnalyses(response.data.analyses);
      setTotalAnalyses(response.data.total);
    } catch (err) {
      setError('Failed to load history. Please try again.');
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (analysisId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this analysis?')) {
      return;
    }
    
    setDeletingId(analysisId);
    try {
      await axios.delete(`http://localhost:8002/history/${analysisId}`);
      // Refresh the list
      fetchHistory();
    } catch (err) {
      alert('Failed to delete analysis');
      console.error('Error deleting analysis:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const handleViewDetails = async (analysisId) => {
    try {
      const response = await axios.get(`http://localhost:8002/history/${analysisId}`);
      onViewAnalysis(response.data);
    } catch (err) {
      alert('Failed to load analysis details');
      console.error('Error fetching analysis:', err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getComplianceColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const totalPages = Math.ceil(totalAnalyses / itemsPerPage);

  return (
    <div className="history-page">
      <div className="history-header">
        <button className="back-button" onClick={onBack}>
          <span className="back-icon">←</span>
          Back to Upload
        </button>
        <h1 className="history-title">
          <span className="title-icon">📋</span>
          Analysis History
        </h1>
        <p className="history-subtitle">View your previously analyzed documents</p>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading history...</p>
        </div>
      ) : error ? (
        <div className="error-container">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button className="retry-button" onClick={fetchHistory}>
            Try Again
          </button>
        </div>
      ) : analyses.length === 0 ? (
        <div className="empty-container">
          <span className="empty-icon">📭</span>
          <h2>No Analysis History</h2>
          <p>You haven't analyzed any documents yet. Upload a document to get started!</p>
          <button className="start-button" onClick={onBack}>
            Upload Document
          </button>
        </div>
      ) : (
        <>
          <div className="history-stats">
            <div className="stat-card">
              <span className="stat-icon">📊</span>
              <div className="stat-info">
                <span className="stat-number">{totalAnalyses}</span>
                <span className="stat-label">Total Analyses</span>
              </div>
            </div>
          </div>

          <div className="history-list">
            {analyses.map((analysis) => (
              <div 
                key={analysis._id} 
                className="history-card"
                onClick={() => handleViewDetails(analysis._id)}
              >
                <div className="card-icon">
                  {documentIcons[analysis.document_type] || documentIcons.other}
                </div>
                <div className="card-content">
                  <h3 className="card-filename">{analysis.filename}</h3>
                  <div className="card-meta">
                    <span className="meta-item">
                      <span className="meta-icon">📁</span>
                      {analysis.document_type || analysis.domain || 'Unknown'}
                    </span>
                    <span className="meta-item">
                      <span className="meta-icon">🕒</span>
                      {formatDate(analysis.analyzed_at)}
                    </span>
                  </div>
                  {analysis.text_snippet && (
                    <p className="card-snippet">
                      {analysis.text_snippet.substring(0, 150)}...
                    </p>
                  )}
                </div>
                <div className="card-score">
                  <div 
                    className="score-circle"
                    style={{ borderColor: getComplianceColor(analysis.compliance_score || 0) }}
                  >
                    <span 
                      className="score-value"
                      style={{ color: getComplianceColor(analysis.compliance_score || 0) }}
                    >
                      {Math.round(analysis.compliance_score || 0)}%
                    </span>
                  </div>
                  <span className="score-label">Compliance</span>
                </div>
                <div className="card-actions">
                  <button 
                    className="action-button view-button"
                    onClick={(e) => { e.stopPropagation(); handleViewDetails(analysis._id); }}
                  >
                    View
                  </button>
                  <button 
                    className="action-button delete-button"
                    onClick={(e) => handleDelete(analysis._id, e)}
                    disabled={deletingId === analysis._id}
                  >
                    {deletingId === analysis._id ? '...' : '🗑️'}
                  </button>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button 
                className="page-button"
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>
              <span className="page-info">
                Page {currentPage} of {totalPages}
              </span>
              <button 
                className="page-button"
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default HistoryPage;
