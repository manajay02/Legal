import React, { useState } from 'react';
import './ComplianceAuditor.css';

function ComplianceAuditor() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [auditResults, setAuditResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('upload'); // upload, processing, results
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedConflict, setSelectedConflict] = useState(null);

  const handleFileChange = (e) => {
    setUploadedFile(e.target.files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
    }
  };

  const startAudit = async () => {
    if (!uploadedFile) {
      alert('Please select a PDF file');
      return;
    }

    setLoading(true);
    setStep('processing');
    setUploadProgress(0);

    // Simulate processing stages
    const stages = [
      { name: 'Extracting Clauses', duration: 500 },
      { name: 'Mapping Statutes', duration: 500 },
      { name: 'Running AI Conflict Detection', duration: 800 },
      { name: 'Generating Report', duration: 300 }
    ];

    let currentProgress = 0;
    for (const stage of stages) {
      await new Promise(resolve => setTimeout(resolve, stage.duration));
      currentProgress += 25;
      setUploadProgress(currentProgress);
    }

    // Simulated audit results
    setAuditResults({
      fileName: uploadedFile.name,
      documentType: 'Employment Contract',
      totalClauses: 12,
      auditDate: new Date().toLocaleDateString(),
      overallCompliance: 58,
      complianceStatus: 'NEEDS ATTENTION',
      clauses: [
        {
          id: 1,
          title: 'Working Hours',
          text: 'Employee shall work 48 hours per week, Monday to Sunday, with no fixed off days.',
          status: 'red',
          severity: 'Critical',
          applicableLaw: 'Shop and Office Employees Act, No. 19 of 1954',
          section: 'Section 7',
          violation: 'Exceeds legal maximum of 45 hours per week and violates mandatory rest day requirement',
          recommendation: 'Reduce to 45 hours per week and provide at least one mandatory off day per week'
        },
        {
          id: 2,
          title: 'Salary Payment',
          text: 'Basic salary of LKR 50,000 per month, paid monthly in cash.',
          status: 'green',
          severity: 'None',
          applicableLaw: 'Payment of Gratuity Act, No. 12 of 1983',
          section: 'General Compliance',
          violation: null,
          recommendation: 'Clause is compliant. Consider adding bank transfer method as an option.'
        },
        {
          id: 3,
          title: 'Notice Period & Termination',
          text: 'Employer can terminate employment with 24 hours notice without cause or compensation.',
          status: 'red',
          severity: 'Critical',
          applicableLaw: 'Industrial Disputes Act, No. 43 of 1950',
          section: 'Section 26 & 27',
          violation: 'Violates statutory minimum notice period and just cause requirement. Unfairly termination clause.',
          recommendation: 'Replace with statutory requirement: minimum 2 weeks notice and just cause for termination'
        },
        {
          id: 4,
          title: 'Leave Entitlement',
          text: 'Annual leave of 7 days per year at employer discretion.',
          status: 'yellow',
          severity: 'High',
          applicableLaw: 'Holidays and Rest Days Act, No. 14 of 1988',
          section: 'Section 23',
          violation: 'Below statutory minimum of 14 days annual leave. Employer discretion conflicts with employee rights.',
          recommendation: 'Increase to minimum 14 days annual leave and make it mandatory, not discretionary'
        },
        {
          id: 5,
          title: 'Probation Period',
          text: 'Probation period of 2 years with no employee rights or protections.',
          status: 'red',
          severity: 'Critical',
          applicableLaw: 'Industrial Disputes Act, No. 43 of 1950',
          section: 'Section 32 & 33',
          violation: 'Excessive probation period (maximum 6 months). No rights during probation violates statutory protections.',
          recommendation: 'Reduce to maximum 6 months and provide basic statutory protections during probation'
        },
        {
          id: 6,
          title: 'Medical Benefits',
          text: 'No medical benefits or health insurance provided.',
          status: 'yellow',
          severity: 'Medium',
          applicableLaw: 'General Labor Standards',
          section: 'Best Practice',
          violation: 'While not strictly illegal, lack of health coverage is below industry standards.',
          recommendation: 'Include mandatory medical/health insurance as per industry practice'
        },
        {
          id: 7,
          title: 'Gratuity',
          text: 'No gratuity entitlement after completion of employment.',
          status: 'red',
          severity: 'Critical',
          applicableLaw: 'Payment of Gratuity Act, No. 12 of 1983',
          section: 'Section 4 & 5',
          violation: 'Gratuity is mandatory by law. Half-month salary per year of service is required.',
          recommendation: 'Include mandatory gratuity: 0.5 month salary per year for first 5 years, 1 month for subsequent years'
        },
        {
          id: 8,
          title: 'Non-Compete Clause',
          text: 'Employee cannot work for competitor companies for 5 years after leaving.',
          status: 'yellow',
          severity: 'High',
          applicableLaw: 'Sri Lankan Contract Law & Competition Act',
          section: 'General Principles',
          violation: '5 years is excessive and may be deemed unreasonable restraint of trade.',
          recommendation: 'Reduce to 1-2 years and limit to specific territory/services to be enforceable'
        }
      ],
      statisticalBreakdown: {
        critical: 4,
        high: 2,
        medium: 2,
        compliant: 2
      },
      applicableLaws: [
        'Shop and Office Employees Act, No. 19 of 1954',
        'Industrial Disputes Act, No. 43 of 1950',
        'Payment of Gratuity Act, No. 12 of 1983',
        'Holidays and Rest Days Act, No. 14 of 1988',
        'Consumer Affairs Authority Act, No. 9 of 2003'
      ]
    });

    setLoading(false);
    setStep('results');
  };

  const resetAudit = () => {
    setUploadedFile(null);
    setAuditResults(null);
    setStep('upload');
    setUploadProgress(0);
    setSelectedConflict(null);
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'red': return '#dc3545';
      case 'yellow': return '#ffc107';
      case 'green': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getStatusLabel = (status) => {
    switch(status) {
      case 'red': return '🔴 ILLEGAL';
      case 'yellow': return '🟡 RISKY';
      case 'green': return '🟢 COMPLIANT';
      default: return '⚪ UNKNOWN';
    }
  };

  return (
    <div className="compliance-auditor">
      {step === 'upload' && (
        <div className="upload-section">
          <div className="upload-container">
            <h2>📋 Automated Civil Compliance Auditor</h2>
            <p>Sri Lankan Statutory Red-Flag Detector</p>

            <div className="auditor-intro">
              <h3>How It Works</h3>
              <div className="workflow-steps">
                <div className="workflow-step">
                  <div className="step-number">1</div>
                  <h4>Upload Document</h4>
                  <p>PDF contracts (Job Offers, Leases, Agreements)</p>
                </div>
                <div className="workflow-step">
                  <div className="step-number">2</div>
                  <h4>Clause Extraction</h4>
                  <p>AI extracts individual legal clauses</p>
                </div>
                <div className="workflow-step">
                  <div className="step-number">3</div>
                  <h4>Statutory Mapping</h4>
                  <p>Matches relevant Sri Lankan Acts</p>
                </div>
                <div className="workflow-step">
                  <div className="step-number">4</div>
                  <h4>Conflict Detection</h4>
                  <p>Identifies legal violations</p>
                </div>
              </div>
            </div>

            <div className="upload-area" onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
              <input
                type="file"
                id="pdfFile"
                onChange={handleFileChange}
                accept=".pdf"
                className="file-input-hidden"
              />
              <label htmlFor="pdfFile" className="upload-label">
                <div className="upload-icon">📄</div>
                <h3>Drag & Drop PDF or Click to Upload</h3>
                <p>Supported formats: PDF (Job Offers, Leases, Contracts)</p>
                {uploadedFile && <p className="file-selected">✓ {uploadedFile.name}</p>}
              </label>
            </div>

            <button
              onClick={startAudit}
              disabled={!uploadedFile || loading}
              className="btn btn-audit"
            >
              {loading ? '⚙️ Processing...' : '🔍 Start Compliance Audit'}
            </button>

            <div className="supported-laws">
              <h4>📚 Statutory Coverage</h4>
              <div className="laws-grid">
                <div className="law-badge">Shop & Office Employees Act, 1954</div>
                <div className="law-badge">Industrial Disputes Act, 1950</div>
                <div className="law-badge">Payment of Gratuity Act, 1983</div>
                <div className="law-badge">Holidays & Rest Days Act, 1988</div>
                <div className="law-badge">Consumer Affairs Authority Act, 2003</div>
                <div className="law-badge">Rent Act, 1833</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {step === 'processing' && (
        <div className="processing-section">
          <div className="processing-container">
            <h2>⚙️ Auditing Document</h2>
            <p>Running compliance check against Sri Lankan statutes...</p>

            <div className="processing-stages">
              <div className="stage">
                <div className="stage-icon">📄</div>
                <p>Extracting Clauses</p>
              </div>
              <div className="stage">
                <div className="stage-icon">📚</div>
                <p>Mapping Statutes</p>
              </div>
              <div className="stage">
                <div className="stage-icon">🤖</div>
                <p>Detecting Conflicts</p>
              </div>
              <div className="stage">
                <div className="stage-icon">📊</div>
                <p>Generating Report</p>
              </div>
            </div>

            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
            </div>
            <p className="progress-text">{uploadProgress}% Complete</p>

            <div className="processing-info">
              <p>📄 File: <strong>{uploadedFile?.name}</strong></p>
              <p>🤖 Model: Sri Lankan Compliance AI v1.0</p>
              <p>⚡ Checking against {auditResults?.applicableLaws.length || 5}+ Sri Lankan Acts</p>
            </div>
          </div>
        </div>
      )}

      {step === 'results' && auditResults && (
        <div className="results-section">
          <div className="results-header">
            <div className="header-info">
              <h2>📊 Compliance Audit Report</h2>
              <p>{auditResults.fileName} • {auditResults.documentType}</p>
              <p className="audit-date">Audit Date: {auditResults.auditDate}</p>
            </div>
          </div>

          {/* Compliance Score */}
          <div className="compliance-score-card">
            <div className="score-circle" style={{ borderColor: getStatusColor(auditResults.complianceStatus === 'NEEDS ATTENTION' ? 'yellow' : 'green') }}>
              <span className="score-number">{auditResults.overallCompliance}%</span>
              <span className="score-label">Compliance Rate</span>
            </div>
            <div className="score-details">
              <h3>{auditResults.complianceStatus}</h3>
              <p>This document has legal issues that need attention before signing.</p>
              <div className="stat-breakdown">
                <div className="stat">
                  <span className="stat-count red">{auditResults.statisticalBreakdown.critical}</span>
                  <span className="stat-label">Critical Issues</span>
                </div>
                <div className="stat">
                  <span className="stat-count yellow">{auditResults.statisticalBreakdown.high}</span>
                  <span className="stat-label">High Risk</span>
                </div>
                <div className="stat">
                  <span className="stat-count">⚠️</span>
                  <span className="stat-label">{auditResults.statisticalBreakdown.medium}</span>
                </div>
                <div className="stat">
                  <span className="stat-count green">{auditResults.statisticalBreakdown.compliant}</span>
                  <span className="stat-label">Compliant</span>
                </div>
              </div>
            </div>
          </div>

          {/* Clause-by-Clause Analysis */}
          <div className="clauses-analysis">
            <h3>📋 Clause-by-Clause Analysis</h3>
            <div className="clauses-list">
              {auditResults.clauses.map((clause, index) => (
                <div
                  key={index}
                  className={`clause-card status-${clause.status}`}
                  onClick={() => setSelectedConflict(selectedConflict === index ? null : index)}
                >
                  <div className="clause-header">
                    <div className="clause-title-section">
                      <h4>{clause.title}</h4>
                      <p className="clause-text">{clause.text}</p>
                    </div>
                    <div className="clause-status-badge" style={{ backgroundColor: getStatusColor(clause.status) }}>
                      {getStatusLabel(clause.status)}
                    </div>
                  </div>

                  {selectedConflict === index && (
                    <div className="clause-details">
                      <div className="detail-row">
                        <span className="detail-label">Applicable Law:</span>
                        <span className="detail-value">{clause.applicableLaw}</span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Section:</span>
                        <span className="detail-value">{clause.section}</span>
                      </div>
                      {clause.violation && (
                        <div className="detail-row violation">
                          <span className="detail-label">❌ Violation:</span>
                          <span className="detail-value">{clause.violation}</span>
                        </div>
                      )}
                      {clause.recommendation && (
                        <div className="detail-row recommendation">
                          <span className="detail-label">✅ Recommendation:</span>
                          <span className="detail-value">{clause.recommendation}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Applicable Laws Reference */}
          <div className="applicable-laws">
            <h3>📚 Applicable Sri Lankan Statutes</h3>
            <div className="laws-list">
              {auditResults.applicableLaws.map((law, index) => (
                <div key={index} className="law-item">
                  <span className="law-icon">⚖️</span>
                  <span className="law-name">{law}</span>
                </div>
              ))}
            </div>
          </div>

          <button onClick={resetAudit} className="btn btn-primary">
            ← Audit Another Document
          </button>
        </div>
      )}
    </div>
  );
}

export default ComplianceAuditor;
