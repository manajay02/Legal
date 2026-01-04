import React, { useState } from 'react';
import './StructuredView.css';

function StructuredView() {
  const [caseInput, setCaseInput] = useState('');
  const [structuredData, setStructuredData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClause, setSelectedClause] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTab, setActiveTab] = useState('laws');

  const handleStructure = async () => {
    if (!caseInput.trim()) {
      alert('Please enter case text');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setStructuredData({
        caseNumber: 'Doe v. ConstructioCorp Matter #4492-B',
        caseType: 'Contract Dispute',
        totalPages: 32,
        sections: [
          {
            id: 1,
            title: 'Definitions',
            status: 'complete',
            clauses: 5
          },
          {
            id: 2,
            title: 'Scope of Services',
            status: 'complete',
            clauses: 8
          },
          {
            id: 3,
            title: 'Compensation',
            status: 'complete',
            clauses: 6
          },
          {
            id: 4,
            title: 'Term & Termination',
            status: 'warning',
            clauses: 9
          },
          {
            id: 5,
            title: 'Detected Termination',
            status: 'complete',
            clauses: 4
          },
          {
            id: 6,
            title: 'Confidentiality',
            status: 'complete',
            clauses: 7
          },
          {
            id: 7,
            title: 'Jurisdiction',
            status: 'complete',
            clauses: 3
          }
        ],
        documentStats: {
          totalSections: 7,
          totalClauses: 38,
          crossReferences: 12,
          ambiguousSections: 2
        },
        currentSection: {
          number: '4',
          title: 'Term & Termination',
          subsections: [
            { id: '4.1', title: 'Term', status: 'complete' },
            { id: '4.2', title: 'Termination', status: 'warning' }
          ]
        },
        documentText: `Contract Agreement #4492

ARTICLE 4: TERM AND TERMINATION

4.1 Term. This Agreement shall commence on the Effective Date and shall continue for a period of thirty (30) days, unless terminated in accordance with this Article 4.

4.2 Termination for Cause: Either Party may terminate this Agreement immediately upon written notice if the other Party breaches any material term of this Agreement and fails to cure such breach within thirty (30) days following receipt of written notice thereof.

In the event of each termination, the terminating Party shall certified all and all remedies available affirm on in equity, subject to the limitations of liability set in Section 8.

4.3 Effect of Termination. Upon expiries, or termination of this Agreement may purced.`,
        currentPage: 14,
        clauseInfo: {
          title: 'Termination for Cause',
          section: 'Section 4.2 • Page 14, Line 12-16',
          status: 'Needs Review',
          issue: 'ambiguous clause boundary',
          text: 'Either Party may terminate this Agreement immediately upon written notice if the other Party breaches any material term of this Agreement and fails to cure such breach within thirty (30) days following receipt of written notice thereof.',
          detectedReferences: 1,
          referencedLaws: [
            {
              name: 'UCC § 2-106(3)',
              status: 'complete',
              description: 'Termination occurs when either party pursuant to a power conferred by the agreement...'
            }
          ],
          citedCases: [
            {
              name: 'UCC § 2-106(3)',
              status: 'warning',
              description: 'Needs reliability verification'
            }
          ],
          parties: 2
        },
        semanticSummary: {
          referencedLaws: [
            {
              name: 'Civil Procedure Code - Sect. 45',
              status: 'good',
              label: 'Well-defined references'
            },
            {
              name: 'UCC § 2-106(3)',
              status: 'warning',
              label: 'Needs reliability verification'
            }
          ],
          citedCases: [
            {
              name: 'Smith v. Johnson',
              status: 'good',
              label: 'Well-defined references'
            },
            {
              name: 'ABC Corp v. XYZ Inc.',
              status: 'warning',
              label: 'Needs reliability verification'
            }
          ],
          parties: [
            { name: 'Party A', role: 'Plaintiff' },
            { name: 'Party B', role: 'Defendant' }
          ]
        }
      });
      setSelectedClause(0);
      setLoading(false);
    }, 1500);
  };

  const handleClauseClick = (index) => {
    setSelectedClause(index);
  };

  const filteredSections = structuredData?.sections.filter(section =>
    section.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="structured-view-analyzer">
      {!structuredData ? (
        <div className="input-container">
          <div className="input-card">
            <h2>📊 Document Structure Analyzer</h2>
            <p>Upload or paste a legal document to extract its structured hierarchy</p>

            <div className="form-group">
              <label>Enter Case Text or Upload Document:</label>
              <textarea
                value={caseInput}
                onChange={(e) => setCaseInput(e.target.value)}
                placeholder="Paste your contract or legal document here..."
                className="text-input"
                rows="15"
              />
            </div>

            <button
              onClick={handleStructure}
              disabled={loading}
              className="btn btn-primary btn-large"
            >
              {loading ? '⚙️ Processing...' : '📄 Analyze Document Structure'}
            </button>
          </div>
        </div>
      ) : (
        <div className="analyzer-layout">
          {/* Header */}
          <div className="analyzer-header">
            <div className="header-title">
              <h1>📑 LexAnalyze</h1>
              <p>{structuredData.caseNumber} • {structuredData.caseType}</p>
            </div>
            <div className="header-tabs">
              <button className="tab-btn">📤 Upload</button>
              <button className="tab-btn">🔍 Analyze</button>
              <button className="tab-btn active">✅ Review</button>
              <button className="tab-btn">📥 Export</button>
            </div>
          </div>

          {/* Main Content */}
          <div className="analyzer-main">
            {/* Left Panel - Document Structure */}
            <div className="left-panel">
              <div className="structure-overview">
                <h3>📋 Document Structure Overview</h3>
                <div className="overview-stats">
                  <div className="stat-item">
                    <span className="stat-label">Total Sections:</span>
                    <span className="stat-value">{structuredData.documentStats.totalSections}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Clauses:</span>
                    <span className="stat-value">{structuredData.documentStats.totalClauses}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Cross-references detected:</span>
                    <span className="stat-value">{structuredData.documentStats.crossReferences}</span>
                  </div>
                  <div className="stat-item warning">
                    <span className="stat-label">⚠️ Ambiguous sections:</span>
                    <span className="stat-value">{structuredData.documentStats.ambiguousSections}</span>
                  </div>
                </div>
              </div>

              <div className="document-outline">
                <h3>📑 Document Outline</h3>
                <div className="search-box">
                  <input
                    type="text"
                    placeholder="Search clauses..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                  />
                </div>

                <div className="outline-list">
                  {filteredSections.map((section, index) => (
                    <div
                      key={index}
                      className={`outline-item ${section.status === 'warning' ? 'warning' : 'complete'}`}
                    >
                      <div className="outline-content">
                        <span className="outline-number">{section.id}.</span>
                        <span className="outline-title">{section.title}</span>
                        <div className="outline-icons">
                          {section.status === 'complete' && <span className="icon">✓</span>}
                          {section.status === 'warning' && <span className="icon warning">⚠️</span>}
                        </div>
                      </div>
                      {section.clauses > 0 && (
                        <span className="clause-count">{section.clauses}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Center Panel - Document Viewer */}
            <div className="center-panel">
              <div className="document-header">
                <div className="page-info">
                  <span className="page-text">Page {structuredData.currentPage} of {structuredData.totalPages}</span>
                  <div className="zoom-controls">
                    <span>100%</span>
                    <span className="divider">•</span>
                    <span className="search-icon">🔍</span>
                  </div>
                </div>
              </div>

              <div className="document-viewer">
                <div className="document-content">
                  {structuredData.documentText}
                </div>
              </div>

              <div className="semantic-summary">
                <h3>📊 Semantic Summary</h3>
                <div className="summary-tabs">
                  <button
                    className={`summary-tab ${activeTab === 'laws' ? 'active' : ''}`}
                    onClick={() => setActiveTab('laws')}
                  >
                    Referenced Laws (2)
                  </button>
                  <button
                    className={`summary-tab ${activeTab === 'cases' ? 'active' : ''}`}
                    onClick={() => setActiveTab('cases')}
                  >
                    Cited Cases (2)
                  </button>
                  <button
                    className={`summary-tab ${activeTab === 'parties' ? 'active' : ''}`}
                    onClick={() => setActiveTab('parties')}
                  >
                    Parties (2)
                  </button>
                </div>

                <div className="summary-content">
                  {activeTab === 'laws' && (
                    <div className="summary-items">
                      {structuredData.semanticSummary.referencedLaws.map((law, idx) => (
                        <div key={idx} className={`summary-item ${law.status}`}>
                          <div className="item-icon">📜</div>
                          <div className="item-content">
                            <p className="item-name">{law.name}</p>
                            <span className={`item-label ${law.status}`}>{law.label}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {activeTab === 'cases' && (
                    <div className="summary-items">
                      {structuredData.semanticSummary.citedCases.map((caseItem, idx) => (
                        <div key={idx} className={`summary-item ${caseItem.status}`}>
                          <div className="item-icon">⚖️</div>
                          <div className="item-content">
                            <p className="item-name">{caseItem.name}</p>
                            <span className={`item-label ${caseItem.status}`}>{caseItem.label}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {activeTab === 'parties' && (
                    <div className="summary-items">
                      {structuredData.semanticSummary.parties.map((party, idx) => (
                        <div key={idx} className="summary-item">
                          <div className="item-icon">👤</div>
                          <div className="item-content">
                            <p className="item-name">{party.name}</p>
                            <span className="item-role">{party.role}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Panel - Clause Info */}
            <div className="right-panel">
              <div className="clause-info">
                <h3>📌 Clause Info</h3>

                <div className="clause-title">
                  <h4>{structuredData.clauseInfo.title}</h4>
                </div>

                <div className="clause-section">
                  <span className="section-location">{structuredData.clauseInfo.section}</span>
                </div>

                <div className="clause-status">
                  {structuredData.clauseInfo.status === 'Needs Review' && (
                    <span className="status-badge warning">
                      {structuredData.clauseInfo.status}
                    </span>
                  )}
                  <span className="status-note">{structuredData.clauseInfo.issue}</span>
                </div>

                <div className="clause-text">
                  <h5>IDENTIFIED CLAUSE TEXT</h5>
                  <p>{structuredData.clauseInfo.text}</p>
                </div>

                <div className="clause-references">
                  <h5>DETECTED REFERENCES: {structuredData.clauseInfo.detectedReferences} Found</h5>

                  <div className="references-section">
                    <h6>Referenced Laws</h6>
                    {structuredData.clauseInfo.referencedLaws.map((law, idx) => (
                      <div key={idx} className={`reference-item ${law.status}`}>
                        <div className="reference-icon">📜</div>
                        <div className="reference-content">
                          <p className="reference-name">{law.name}</p>
                          <p className="reference-desc">{law.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="references-section">
                    <h6>Cited Cases</h6>
                    {structuredData.clauseInfo.citedCases.map((caseItem, idx) => (
                      <div key={idx} className={`reference-item ${caseItem.status}`}>
                        <div className="reference-icon">⚖️</div>
                        <div className="reference-content">
                          <p className="reference-name">{caseItem.name}</p>
                          <p className="reference-desc">{caseItem.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StructuredView;
