import React, { useState } from 'react';
import '../styles/MandatoryClausesPage.css';

function MandatoryClausesPage({ results, fileName, onBack }) {
  const { domain, clauses, missing_mandatory } = results;
  const [downloading, setDownloading] = useState(false);

  // Define mandatory clauses for different contract types
  const mandatoryClausesMap = {
    employment: [
      { name: 'Salary / Compensation', description: 'Clear statement of monthly/annual salary and payment terms' },
      { name: 'Working Hours', description: 'Standard working hours as per Shop and Office Employees Act' },
      { name: 'EPF Contribution', description: 'Employees Provident Fund contribution details' },
      { name: 'ETF Contribution', description: 'Employees Trust Fund contribution details' },
      { name: 'Leave Policy', description: 'Annual leave, sick leave, and other leave entitlements' },
      { name: 'Termination Clause', description: 'Notice period and termination conditions' },
      { name: 'Probation Period', description: 'Duration and conditions of probationary period' },
      { name: 'Job Description', description: 'Clear definition of roles and responsibilities' }
    ],
    rent: [
      { name: 'Rent Amount', description: 'Monthly rent and payment due date' },
      { name: 'Security Deposit', description: 'Amount and conditions for refund' },
      { name: 'Lease Duration', description: 'Start and end date of tenancy' },
      { name: 'Maintenance Responsibility', description: 'Who handles repairs and maintenance' },
      { name: 'Termination Notice', description: 'Required notice period for ending lease' },
      { name: 'Property Description', description: 'Address and description of rental property' },
      { name: 'Utilities', description: 'Who pays for electricity, water, etc.' }
    ],
    sale: [
      { name: 'Purchase Price', description: 'Total sale price and payment terms' },
      { name: 'Property Description', description: 'Legal description of the property' },
      { name: 'Title Deed', description: 'Evidence of clear title ownership' },
      { name: 'Payment Schedule', description: 'Advance, installments, and final payment' },
      { name: 'Possession Date', description: 'When buyer takes possession' },
      { name: 'Warranties', description: 'Seller warranties about property condition' }
    ],
    general: [
      { name: 'Parties Identification', description: 'Clear identification of all parties' },
      { name: 'Subject Matter', description: 'Clear description of contract subject' },
      { name: 'Terms & Conditions', description: 'Main obligations of parties' },
      { name: 'Duration', description: 'Contract validity period' },
      { name: 'Termination', description: 'Conditions for ending the contract' },
      { name: 'Dispute Resolution', description: 'How disputes will be resolved' }
    ]
  };

  // Get the appropriate mandatory clauses based on domain
  const domainKey = domain?.toLowerCase() || 'general';
  const allMandatoryClauses = mandatoryClausesMap[domainKey] || mandatoryClausesMap.general;

  // Determine which mandatory clauses are present and missing
  const missingClauseNames = missing_mandatory?.map(m => m.clause.toLowerCase()) || [];
  
  // Check which clauses from the document match mandatory requirements
  const presentClauseTexts = clauses?.map(c => c.clause.toLowerCase()) || [];
  
  const analyzedClauses = allMandatoryClauses.map(mandatory => {
    const isMissing = missingClauseNames.some(name => 
      mandatory.name.toLowerCase().includes(name) || name.includes(mandatory.name.toLowerCase())
    );
    
    // Check if any clause in the document relates to this mandatory clause
    const isPresent = !isMissing && presentClauseTexts.some(text =>
      text.includes(mandatory.name.toLowerCase().split('/')[0].trim()) ||
      text.includes(mandatory.name.toLowerCase().split(' ')[0])
    );

    return {
      ...mandatory,
      status: isMissing ? 'missing' : 'present'
    };
  });

  // For better accuracy, explicitly mark missing ones from the API
  const presentClauses = analyzedClauses.filter(c => c.status === 'present');
  const missingClauses = analyzedClauses.filter(c => c.status === 'missing');

  // Add any additional missing clauses from the API that weren't in our predefined list
  const additionalMissing = missing_mandatory?.filter(m => 
    !allMandatoryClauses.some(mc => 
      mc.name.toLowerCase().includes(m.clause.toLowerCase()) || 
      m.clause.toLowerCase().includes(mc.name.toLowerCase())
    )
  ) || [];

  const getDomainDisplayName = () => {
    const names = {
      employment: 'Employee Contract',
      rent: 'Rental Agreement',
      sale: 'Sale Agreement',
      general: 'General Contract'
    };
    return names[domainKey] || 'Contract';
  };

  const generateReport = () => {
    setDownloading(true);
    
    const reportDate = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    let reportContent = `
═══════════════════════════════════════════════════════════════════════════════
                    MANDATORY CLAUSES COMPLIANCE REPORT
═══════════════════════════════════════════════════════════════════════════════

Generated: ${reportDate}
Document: ${fileName}
Contract Type: ${getDomainDisplayName()} (Sri Lanka)

═══════════════════════════════════════════════════════════════════════════════
                         SUMMARY
═══════════════════════════════════════════════════════════════════════════════

Total Mandatory Clauses Required: ${allMandatoryClauses.length}
Clauses Present: ${presentClauses.length}
Clauses Missing: ${missingClauses.length + additionalMissing.length}
Compliance Rate: ${Math.round((presentClauses.length / allMandatoryClauses.length) * 100)}%

═══════════════════════════════════════════════════════════════════════════════
                    ✅ MANDATORY CLAUSES FOR ${getDomainDisplayName().toUpperCase()}
═══════════════════════════════════════════════════════════════════════════════

${allMandatoryClauses.map((c, i) => `${i + 1}. ${c.name}
   ${c.description}`).join('\n\n')}

═══════════════════════════════════════════════════════════════════════════════
                    📄 UPLOADED DOCUMENT CONTAINS
═══════════════════════════════════════════════════════════════════════════════

${presentClauses.length > 0 ? presentClauses.map(c => `✔ ${c.name}`).join('\n') : 'No mandatory clauses detected'}

═══════════════════════════════════════════════════════════════════════════════
                    ❌ MISSING CLAUSES
═══════════════════════════════════════════════════════════════════════════════

${missingClauses.length > 0 || additionalMissing.length > 0 
  ? [...missingClauses.map(c => `✗ ${c.name}\n  Requirement: ${c.description}`), 
     ...additionalMissing.map(c => `✗ ${c.clause}\n  Legal Basis: ${c.rule || 'N/A'}`)].join('\n\n')
  : 'All mandatory clauses are present ✓'}

═══════════════════════════════════════════════════════════════════════════════
                    RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════

${missingClauses.length > 0 || additionalMissing.length > 0 
  ? `The following actions are recommended to ensure legal compliance:

${[...missingClauses, ...additionalMissing].map((c, i) => 
  `${i + 1}. Add ${c.name || c.clause} clause to the contract`
).join('\n')}

Please consult with a legal professional to draft appropriate clauses
that comply with Sri Lankan law.`
  : 'Your document contains all mandatory clauses. No immediate action required.'}

═══════════════════════════════════════════════════════════════════════════════
                    LEGAL DISCLAIMER
═══════════════════════════════════════════════════════════════════════════════

This report is generated by an AI-powered compliance checking system and is
provided for informational purposes only. It does not constitute legal advice.
Please consult with a qualified legal professional for specific legal matters.

Generated by: Civil Compliance Auditor
Technology: Legal-BERT NLI (Natural Language Inference)

═══════════════════════════════════════════════════════════════════════════════
`;

    // Create and download the file
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Mandatory_Clauses_Report_${fileName.replace(/\.[^/.]+$/, '')}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    setTimeout(() => setDownloading(false), 1000);
  };

  const generatePDFReport = () => {
    setDownloading(true);
    
    // Create HTML content for PDF
    const reportDate = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Mandatory Clauses Compliance Report</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; }
    h1 { color: #1a365d; border-bottom: 3px solid #1a365d; padding-bottom: 10px; }
    h2 { color: #2d3748; margin-top: 30px; }
    .header { text-align: center; margin-bottom: 40px; }
    .summary { background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
    .stat { padding: 15px; background: white; border-radius: 8px; text-align: center; }
    .stat-value { font-size: 24px; font-weight: bold; }
    .present { color: #22c55e; }
    .missing { color: #ef4444; }
    .clause-item { padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
    .check { color: #22c55e; font-weight: bold; }
    .cross { color: #ef4444; font-weight: bold; }
    .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #718096; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📋 Mandatory Clauses Compliance Report</h1>
    <p><strong>Document:</strong> ${fileName}</p>
    <p><strong>Contract Type:</strong> ${getDomainDisplayName()} (Sri Lanka)</p>
    <p><strong>Generated:</strong> ${reportDate}</p>
  </div>
  
  <div class="summary">
    <h2>Summary</h2>
    <div class="summary-grid">
      <div class="stat">
        <div class="stat-value">${allMandatoryClauses.length}</div>
        <div>Required Clauses</div>
      </div>
      <div class="stat">
        <div class="stat-value present">${presentClauses.length}</div>
        <div>Present</div>
      </div>
      <div class="stat">
        <div class="stat-value missing">${missingClauses.length + additionalMissing.length}</div>
        <div>Missing</div>
      </div>
      <div class="stat">
        <div class="stat-value">${Math.round((presentClauses.length / allMandatoryClauses.length) * 100)}%</div>
        <div>Compliance</div>
      </div>
    </div>
  </div>
  
  <h2>✅ Mandatory Clauses for ${getDomainDisplayName()}</h2>
  ${allMandatoryClauses.map(c => `<div class="clause-item"><strong>${c.name}</strong><br><small>${c.description}</small></div>`).join('')}
  
  <h2>📄 Present in Document</h2>
  ${presentClauses.length > 0 
    ? presentClauses.map(c => `<div class="clause-item"><span class="check">✔</span> ${c.name}</div>`).join('')
    : '<p>No mandatory clauses detected</p>'}
  
  <h2>❌ Missing Clauses</h2>
  ${missingClauses.length > 0 || additionalMissing.length > 0
    ? [...missingClauses.map(c => `<div class="clause-item"><span class="cross">✗</span> ${c.name}<br><small>${c.description}</small></div>`),
       ...additionalMissing.map(c => `<div class="clause-item"><span class="cross">✗</span> ${c.clause}<br><small>${c.rule || ''}</small></div>`)].join('')
    : '<p class="present">All mandatory clauses are present ✓</p>'}
  
  <div class="footer">
    <p><strong>Disclaimer:</strong> This report is generated by an AI system for informational purposes only. It does not constitute legal advice.</p>
    <p>Generated by Civil Compliance Auditor | Legal-BERT NLI</p>
  </div>
</body>
</html>
`;

    // Open in new window for printing
    const printWindow = window.open('', '_blank');
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.print();
    
    setTimeout(() => setDownloading(false), 1000);
  };

  return (
    <div className="mandatory-page">
      {/* Navigation */}
      <div className="mandatory-nav">
        <button className="nav-btn back-btn" onClick={onBack}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          <span>Back to Results</span>
        </button>
        <div className="nav-actions">
          <button 
            className="nav-btn download-btn" 
            onClick={generateReport}
            disabled={downloading}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <span>{downloading ? 'Generating...' : 'Download TXT'}</span>
          </button>
          <button 
            className="nav-btn download-btn primary" 
            onClick={generatePDFReport}
            disabled={downloading}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <span>{downloading ? 'Generating...' : 'Print Report'}</span>
          </button>
        </div>
      </div>

      {/* Page Header */}
      <div className="mandatory-header">
        <div className="header-content">
          <h1>Mandatory Clauses Analysis</h1>
          <p className="header-subtitle">
            Review required clauses for <strong>{getDomainDisplayName()}</strong> under Sri Lankan law
          </p>
        </div>
        <div className="document-info">
          <span className="doc-icon">📄</span>
          <div className="doc-details">
            <span className="doc-name">{fileName}</span>
            <span className="doc-type">{getDomainDisplayName()}</span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="mandatory-summary">
        <div className="summary-card required">
          <div className="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
            </svg>
          </div>
          <div className="card-content">
            <span className="card-value">{allMandatoryClauses.length}</span>
            <span className="card-label">Required Clauses</span>
          </div>
        </div>
        <div className="summary-card present">
          <div className="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22,4 12,14.01 9,11.01"/>
            </svg>
          </div>
          <div className="card-content">
            <span className="card-value">{presentClauses.length}</span>
            <span className="card-label">Present</span>
          </div>
        </div>
        <div className="summary-card missing">
          <div className="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <div className="card-content">
            <span className="card-value">{missingClauses.length + additionalMissing.length}</span>
            <span className="card-label">Missing</span>
          </div>
        </div>
        <div className="summary-card compliance">
          <div className="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className="card-content">
            <span className="card-value">{Math.round((presentClauses.length / allMandatoryClauses.length) * 100)}%</span>
            <span className="card-label">Compliance</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="mandatory-content">
        {/* All Required Clauses */}
        <div className="content-section all-clauses">
          <div className="section-header">
            <div className="header-icon required">✅</div>
            <h2>Mandatory Clauses for {getDomainDisplayName()} (Sri Lanka)</h2>
          </div>
          <div className="clauses-list">
            {allMandatoryClauses.map((clause, index) => (
              <div key={index} className="clause-item">
                <div className="item-number">{index + 1}</div>
                <div className="item-content">
                  <span className="item-name">{clause.name}</span>
                  <span className="item-description">{clause.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="two-column">
          {/* Present Clauses */}
          <div className="content-section present-clauses">
            <div className="section-header">
              <div className="header-icon present">📄</div>
              <h2>Uploaded Document Contains</h2>
            </div>
            <div className="clauses-list">
              {presentClauses.length > 0 ? (
                presentClauses.map((clause, index) => (
                  <div key={index} className="clause-item present">
                    <div className="item-status">✔</div>
                    <div className="item-content">
                      <span className="item-name">{clause.name}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">📋</span>
                  <p>No mandatory clauses detected in the document</p>
                </div>
              )}
            </div>
          </div>

          {/* Missing Clauses */}
          <div className="content-section missing-clauses">
            <div className="section-header">
              <div className="header-icon missing">❌</div>
              <h2>Missing Clauses</h2>
            </div>
            <div className="clauses-list">
              {missingClauses.length > 0 || additionalMissing.length > 0 ? (
                <>
                  {missingClauses.map((clause, index) => (
                    <div key={`missing-${index}`} className="clause-item missing">
                      <div className="item-status">✗</div>
                      <div className="item-content">
                        <span className="item-name">{clause.name}</span>
                        <span className="item-description">{clause.description}</span>
                      </div>
                    </div>
                  ))}
                  {additionalMissing.map((clause, index) => (
                    <div key={`additional-${index}`} className="clause-item missing">
                      <div className="item-status">✗</div>
                      <div className="item-content">
                        <span className="item-name">{clause.clause}</span>
                        {clause.rule && <span className="item-description">{clause.rule}</span>}
                      </div>
                    </div>
                  ))}
                </>
              ) : (
                <div className="empty-state success">
                  <span className="empty-icon">🎉</span>
                  <p>All mandatory clauses are present!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations Section */}
      {(missingClauses.length > 0 || additionalMissing.length > 0) && (
        <div className="recommendations-section">
          <div className="section-header">
            <div className="header-icon warning">💡</div>
            <h2>Recommendations</h2>
          </div>
          <div className="recommendations-content">
            <p className="recommendations-intro">
              To ensure your {getDomainDisplayName().toLowerCase()} complies with Sri Lankan law, 
              please consider adding the following clauses:
            </p>
            <ul className="recommendations-list">
              {[...missingClauses, ...additionalMissing].map((clause, index) => (
                <li key={index}>
                  Add <strong>{clause.name || clause.clause}</strong> clause to the contract
                </li>
              ))}
            </ul>
            <div className="disclaimer">
              <span className="disclaimer-icon">⚠️</span>
              <p>
                This analysis is provided for informational purposes only and does not constitute legal advice. 
                Please consult with a qualified legal professional for specific legal matters.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MandatoryClausesPage;
