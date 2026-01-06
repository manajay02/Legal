import React, { useState, useEffect } from 'react';
import './CasesDatabase.css';
import caseService from '../services/caseService';

function CasesDatabase() {
  const [cases, setCases] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedType, setSelectedType] = useState(null);
  const [expandedCase, setExpandedCase] = useState(null);
  const [error, setError] = useState(null);

  const caseTypes = [
    'Civil', 'Criminal', 'Labour', 'Family', 'Financial',
    'Drug', 'Environmental', 'Tax', 'Terrorism', 'Sexual Cases',
    'Sports', 'Asset', 'Contempt of Court'
  ];

  const loadCases = async () => {
    try {
      setLoading(true);
      const response = await caseService.getStoredCases(selectedType, currentPage);
      setCases(response.data.cases || []);
      setError(null);
    } catch (err) {
      console.error('Error loading cases:', err);
      setError('Error loading cases from database');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await caseService.getCaseStats();
      setStats(response.data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  useEffect(() => {
    loadCases();
    loadStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedType, currentPage]);

  const handleDeleteCase = async (caseId) => {
    if (window.confirm('Are you sure you want to delete this case?')) {
      try {
        await caseService.deleteCase(caseId);
        loadCases();
        loadStats();
        alert('Case deleted successfully');
      } catch (err) {
        alert('Error deleting case');
      }
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      'Civil': '#3498db',
      'Criminal': '#e74c3c',
      'Labour': '#2ecc71',
      'Family': '#9b59b6',
      'Financial': '#f39c12',
      'Drug': '#c0392b',
      'Environmental': '#16a085',
      'Tax': '#8e44ad',
      'Terrorism': '#34495e',
      'Sexual Cases': '#d35400',
      'Sports': '#1abc9c',
      'Asset': '#7f8c8d',
      'Contempt of Court': '#c0392b'
    };
    return colors[type] || '#95a5a6';
  };

  return (
    <div className="container">
      <h2>📚 Cases Database</h2>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        View all stored cases with analytics and statistics
      </p>

      {/* Statistics Section */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '1rem',
          marginBottom: '2rem'
        }}>
          {/* Total Cases */}
          <div style={{
            background: '#fff',
            border: '1px solid #eee',
            borderRadius: '8px',
            padding: '1.5rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <div style={{ fontSize: '0.85rem', color: '#999', marginBottom: '0.5rem' }}>
              TOTAL CASES
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1e3c72' }}>
              {stats.totalCases}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.5rem' }}>
              Stored in database
            </div>
          </div>

          {/* Cases by Type (showing top 3) */}
          {stats.casesByType.slice(0, 3).map(item => (
            <div key={item._id} style={{
              background: '#fff',
              border: `2px solid ${getTypeColor(item._id)}`,
              borderRadius: '8px',
              padding: '1.5rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '0.85rem', color: '#999', marginBottom: '0.5rem' }}>
                {item._id}
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: getTypeColor(item._id) }}>
                {item.count}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.5rem' }}>
                cases
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Case Type Filter */}
      <div style={{
        background: '#f8f9fa',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '2rem'
      }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
          Filter by Case Type:
        </label>
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          flexWrap: 'wrap'
        }}>
          <button
            onClick={() => {
              setSelectedType(null);
              setCurrentPage(1);
            }}
            style={{
              padding: '0.5rem 1rem',
              background: selectedType === null ? '#1e3c72' : '#e0e0e0',
              color: selectedType === null ? 'white' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            All Types
          </button>
          {caseTypes.map(type => (
            <button
              key={type}
              onClick={() => {
                setSelectedType(type);
                setCurrentPage(1);
              }}
              style={{
                padding: '0.5rem 1rem',
                background: selectedType === type ? getTypeColor(type) : '#e0e0e0',
                color: selectedType === type ? 'white' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: selectedType === type ? '600' : '400'
              }}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div style={{
          background: '#ffe8e8',
          border: '1px solid #dc3545',
          color: '#dc3545',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem'
        }}>
          {error}
        </div>
      )}

      {/* Cases List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p>Loading cases...</p>
        </div>
      ) : cases.length === 0 ? (
        <div style={{
          background: '#f0f4f8',
          padding: '2rem',
          borderRadius: '8px',
          textAlign: 'center',
          color: '#666'
        }}>
          <p>No cases found in database</p>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Add a case using the "Add Case" section to get started
          </p>
        </div>
      ) : (
        <>
          <div style={{ marginBottom: '1rem', color: '#666' }}>
            Showing <strong>{cases.length}</strong> case{cases.length !== 1 ? 's' : ''}
          </div>

          {cases.map(caseItem => (
            <div key={caseItem._id} style={{
              background: '#fff',
              border: `1px solid ${getTypeColor(caseItem.caseType)}`,
              borderLeft: `4px solid ${getTypeColor(caseItem.caseType)}`,
              borderRadius: '8px',
              padding: '1.5rem',
              marginBottom: '1rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '1rem'
              }}>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: '#1e3c72' }}>
                    {caseItem.title}
                  </h3>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{
                      background: getTypeColor(caseItem.caseType),
                      color: 'white',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '20px',
                      fontSize: '0.85rem',
                      fontWeight: '600'
                    }}>
                      {caseItem.caseType}
                    </span>
                    <span style={{ color: '#999', fontSize: '0.9rem' }}>
                      📅 {caseItem.year}
                    </span>
                    {caseItem.court && (
                      <span style={{ color: '#999', fontSize: '0.9rem' }}>
                        ⚖️ {caseItem.court}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => setExpandedCase(expandedCase === caseItem._id ? null : caseItem._id)}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#1e3c72',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.85rem'
                    }}
                  >
                    {expandedCase === caseItem._id ? '📖 Hide Details' : '📖 View Details'}
                  </button>
                  <button
                    onClick={() => handleDeleteCase(caseItem._id)}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.85rem'
                    }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>

              {/* Summary */}
              <p style={{
                color: '#555',
                lineHeight: '1.6',
                marginBottom: '1rem',
                borderBottom: '1px solid #eee',
                paddingBottom: '1rem'
              }}>
                {caseItem.summary}
              </p>

              {/* Analytics */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem',
                marginBottom: '1rem'
              }}>
                <div style={{ background: '#f8f9fa', padding: '0.75rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8rem', color: '#999' }}>KEY POINTS</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e3c72' }}>
                    {caseItem.analytics.keyPointsCount}
                  </div>
                </div>
                <div style={{ background: '#f8f9fa', padding: '0.75rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8rem', color: '#999' }}>SUMMARY LENGTH</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#2ecc71' }}>
                    {caseItem.analytics.summaryLength}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#999' }}>characters</div>
                </div>
                <div style={{ background: '#f8f9fa', padding: '0.75rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8rem', color: '#999' }}>AGE</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f39c12' }}>
                    {caseItem.analytics.yearsOld}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#999' }}>years</div>
                </div>
                <div style={{ background: '#f8f9fa', padding: '0.75rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.8rem', color: '#999' }}>OUTCOME</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#1e3c72' }}>
                    {caseItem.outcome}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedCase === caseItem._id && (
                <div style={{
                  background: '#f0f4f8',
                  padding: '1rem',
                  borderRadius: '4px',
                  borderTop: '1px solid #ddd',
                  marginTop: '1rem'
                }}>
                  {/* Key Points */}
                  {caseItem.keyPoints && caseItem.keyPoints.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: '#1e3c72' }}>Key Points:</strong>
                      <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {caseItem.keyPoints.map((point, idx) => (
                          <li key={idx} style={{ color: '#555', marginBottom: '0.25rem' }}>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Case ID */}
                  <div style={{ fontSize: '0.8rem', color: '#999', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #ddd' }}>
                    <strong>Database ID:</strong> {caseItem._id}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Pagination */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '0.5rem',
            marginTop: '2rem'
          }}>
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              style={{
                padding: '0.5rem 1rem',
                background: currentPage === 1 ? '#ccc' : '#1e3c72',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
              }}
            >
              ← Previous
            </button>
            <span style={{ padding: '0.5rem 1rem', color: '#666' }}>
              Page {currentPage}
            </span>
            <button
              onClick={() => setCurrentPage(prev => prev + 1)}
              style={{
                padding: '0.5rem 1rem',
                background: '#1e3c72',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Next →
            </button>
          </div>
        </>
      )}

      {/* Info Box */}
      <div style={{
        background: '#f0f4f8',
        padding: '1.5rem',
        borderRadius: '8px',
        marginTop: '2rem',
        borderLeft: '4px solid #1e3c72'
      }}>
        <h4>💡 About the Database</h4>
        <ul>
          <li>All cases are stored in MongoDB</li>
          <li>Cases can be searched for similarity matching</li>
          <li>Analytics track case characteristics</li>
          <li>Delete cases to manage the database</li>
          <li>Use filters to view specific case types</li>
        </ul>
      </div>
    </div>
  );
}

export default CasesDatabase;
