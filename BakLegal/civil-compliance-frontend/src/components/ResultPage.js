import React, { useState, useMemo, useRef } from 'react';
import '../styles/ResultPage.css';

function ResultPage({ results, onBack, onViewMandatory, onViewActs, activeFilter, setActiveFilter }) {
  const { domain, clauses, present_mandatory, missing_mandatory, document_type } = results;
  const [expandedCards, setExpandedCards] = useState({});
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Refs for scrolling to sections
  const clauseDetailsRef = useRef(null);

  // Mandatory clauses definition for different document types
  const mandatoryClausesByType = {
    employment: {
      name: 'Employment Contract',
      icon: '👔',
      clauses: [
        { id: 'salary', name: 'Salary/Compensation', description: 'Monthly salary, payment schedule, and method' },
        { id: 'working_hours', name: 'Working Hours', description: 'Daily and weekly working hours as per Shop and Office Act' },
        { id: 'epf', name: 'EPF Contributions', description: 'Employees\' Provident Fund contributions (8% employee, 12% employer)' },
        { id: 'etf', name: 'ETF Contributions', description: 'Employees\' Trust Fund contributions (3% employer)' },
        { id: 'leave_policy', name: 'Leave Policy', description: 'Annual leave, sick leave, and casual leave entitlements' },
        { id: 'termination', name: 'Termination Clause', description: 'Notice period, termination conditions, and severance' },
        { id: 'probation', name: 'Probation Period', description: 'Duration and conditions of probationary period' },
        { id: 'job_description', name: 'Job Description', description: 'Duties and responsibilities of the employee' },
        { id: 'maternity', name: 'Maternity Benefits', description: 'Maternity leave as per Maternity Benefits Ordinance' },
        { id: 'overtime', name: 'Overtime Provisions', description: 'Overtime rates and conditions' },
        { id: 'gratuity', name: 'Gratuity Entitlement', description: 'Gratuity payment upon completion of service' },
        { id: 'notice_period', name: 'Notice Period & Severance', description: 'Required notice period for termination' },
        { id: 'minimum_wage', name: 'Minimum Wages', description: 'Compliance with minimum wage requirements' },
        { id: 'employee_identification', name: 'Employee Name & Job Title', description: 'Clear identification of employee and position' },
      ]
    },
    rental: {
      name: 'Rental Agreement',
      icon: '🏠',
      clauses: [
        { id: 'parties', name: 'Parties\' Names & Addresses', description: 'Full names and addresses of landlord and tenant' },
        { id: 'property_description', name: 'Description of Property', description: 'Clear description of the rental property' },
        { id: 'rent_amount', name: 'Rent Amount & Payment Method', description: 'Monthly rent and payment terms' },
        { id: 'duration', name: 'Duration of Tenancy', description: 'Start and end date of tenancy period' },
        { id: 'security_deposit', name: 'Security Deposit', description: 'Deposit amount and refund conditions' },
        { id: 'termination_notice', name: 'Termination / Notice Period', description: 'Notice period for ending tenancy' },
        { id: 'rights_obligations', name: 'Rights & Obligations', description: 'Rights and duties of tenant and landlord' },
        { id: 'registration', name: 'Registration of Agreement', description: 'Registration of Documents Ordinance compliance' },
      ]
    },
    finance_leasing: {
      name: 'Finance Leasing Agreement',
      icon: '🚗',
      clauses: [
        { id: 'lease_rental', name: 'Lease Rental Amount', description: 'Monthly lease rental payment amount' },
        { id: 'lease_term', name: 'Lease Term/Period', description: 'Duration of the lease' },
        { id: 'asset_description', name: 'Equipment/Vehicle Description', description: 'Detailed description of the leased asset' },
        { id: 'insurance', name: 'Insurance Requirements', description: 'Insurance obligations for the leased asset' },
        { id: 'repossession', name: 'Repossession Rights', description: 'Conditions under which asset can be repossessed' },
        { id: 'ownership_transfer', name: 'Ownership Transfer', description: 'Terms for transfer of ownership at end of lease' },
      ]
    },
    consumer: {
      name: 'Loan/Credit Agreement',
      icon: '💰',
      clauses: [
        { id: 'loan_amount', name: 'Loan/Principal Amount', description: 'The principal loan amount clearly stated' },
        { id: 'interest_rate', name: 'Interest Rate & Calculation', description: 'Interest rate and how it is calculated' },
        { id: 'repayment_schedule', name: 'Repayment Schedule', description: 'Installments, due dates, and repayment terms' },
        { id: 'borrower_rights', name: 'Borrower Rights', description: 'Early settlement rights, complaint procedures' },
        { id: 'late_payment_penalty', name: 'Late Payment Penalty', description: 'Reasonable and legally permitted late fees' },
        { id: 'debt_recovery', name: 'Debt Recovery Procedures', description: 'Collection and recovery procedures' },
      ]
    },
    partnership: {
      name: 'Partnership Agreement',
      icon: '🤝',
      clauses: [
        { id: 'partners', name: 'Partners\' Names & Capital', description: 'Names of all partners and their capital contributions' },
        { id: 'profit_sharing', name: 'Profit/Loss Sharing Ratio', description: 'How profits and losses are divided' },
        { id: 'duties', name: 'Duties & Responsibilities', description: 'Roles and responsibilities of each partner' },
        { id: 'decision_making', name: 'Decision-Making Authority', description: 'How decisions are made in the partnership' },
        { id: 'partnership_duration', name: 'Duration of Partnership', description: 'How long the partnership will last' },
        { id: 'dissolution', name: 'Termination/Dissolution Terms', description: 'How the partnership can be ended' },
      ]
    },
    general: {
      name: 'Legal Document',
      icon: '📄',
      clauses: [
        { id: 'parties', name: 'Parties Identification', description: 'Names and details of all parties' },
        { id: 'terms', name: 'Terms & Conditions', description: 'Main terms of the agreement' },
        { id: 'signatures', name: 'Signatures', description: 'Signature requirements' },
      ]
    },
    other: {
      name: 'Legal Document',
      icon: '📄',
      clauses: [
        { id: 'parties', name: 'Parties Involved', description: 'Names and details of parties' },
        { id: 'terms', name: 'Terms & Conditions', description: 'Main terms of agreement' },
        { id: 'signatures', name: 'Signatures', description: 'Signature requirements' },
      ]
    }
  };

  const docType = document_type || domain || 'other';
  const currentDocType = mandatoryClausesByType[docType] || mandatoryClausesByType.other;

  // Categorize clauses
  const categorizedClauses = useMemo(() => {
    if (!clauses) return { entailment: [], contradiction: [], neutral: [] };
    
    return {
      entailment: clauses.filter(c => 
        c.prediction?.toLowerCase() === 'entailment' || 
        c.status === '🟢 Compliant'
      ),
      contradiction: clauses.filter(c => 
        c.prediction?.toLowerCase() === 'contradiction' || 
        c.status === '🔴 Violation'
      ),
      neutral: clauses.filter(c => 
        c.prediction?.toLowerCase() === 'neutral' || 
        c.status === '🟡 Needs Review'
      )
    };
  }, [clauses]);

  // Calculate statistics
  const stats = useMemo(() => {
    const total = clauses?.length || 0;
    const compliant = categorizedClauses.entailment.length;
    const nonCompliant = categorizedClauses.contradiction.length;
    const needsReview = categorizedClauses.neutral.length;
    
    return {
      total,
      compliant,
      nonCompliant,
      needsReview,
      compliantPercent: total > 0 ? ((compliant / total) * 100).toFixed(1) : 0,
      nonCompliantPercent: total > 0 ? ((nonCompliant / total) * 100).toFixed(1) : 0,
      neutralPercent: total > 0 ? ((needsReview / total) * 100).toFixed(1) : 0,
    };
  }, [clauses, categorizedClauses]);

  // Mandatory analysis
  const mandatoryAnalysis = useMemo(() => {
    const present = [];
    const missing = [];
    
    if (present_mandatory && present_mandatory.length > 0) {
      present_mandatory.forEach(backendClause => {
        const matchingFrontendClause = currentDocType.clauses.find(
          fc => fc.id === backendClause.id || 
                fc.name.toLowerCase().includes(backendClause.clause?.toLowerCase().split('/')[0]) ||
                backendClause.clause?.toLowerCase().includes(fc.id.replace('_', ' '))
        );
        if (matchingFrontendClause) {
          present.push({
            ...matchingFrontendClause,
            confidence: backendClause.confidence,
            legal_basis: backendClause.legal_basis
          });
        } else {
          present.push({
            id: backendClause.id,
            name: backendClause.clause,
            description: backendClause.legal_basis || '',
            confidence: backendClause.confidence
          });
        }
      });
    }
    
    if (missing_mandatory && missing_mandatory.length > 0) {
      missing_mandatory.forEach(backendClause => {
        const matchingFrontendClause = currentDocType.clauses.find(
          fc => fc.id === backendClause.id || 
                fc.name.toLowerCase().includes(backendClause.clause?.toLowerCase().split('/')[0]) ||
                backendClause.clause?.toLowerCase().includes(fc.id.replace('_', ' '))
        );
        if (matchingFrontendClause) {
          missing.push({
            ...matchingFrontendClause,
            legal_basis: backendClause.legal_basis,
            rule: backendClause.rule
          });
        } else {
          missing.push({
            id: backendClause.id,
            name: backendClause.clause,
            description: backendClause.legal_basis || '',
            rule: backendClause.rule
          });
        }
      });
    }
    
    if ((!present_mandatory || present_mandatory.length === 0) && 
        (!missing_mandatory || missing_mandatory.length === 0)) {
      currentDocType.clauses.forEach(mandatoryClause => {
        const isPresent = clauses?.some(c => {
          const clauseText = (c.clause || '').toLowerCase();
          const keywords = mandatoryClause.id.split('_');
          return keywords.some(kw => clauseText.includes(kw));
        });
        if (isPresent) {
          present.push(mandatoryClause);
        } else {
          missing.push(mandatoryClause);
        }
      });
    }

    return { present, missing };
  }, [clauses, present_mandatory, missing_mandatory, currentDocType]);

  // Get filtered clauses based on active filter
  const filteredClauses = useMemo(() => {
    if (activeFilter === 'all') return clauses || [];
    if (activeFilter === 'compliant') return categorizedClauses.entailment;
    if (activeFilter === 'non-compliant') return categorizedClauses.contradiction;
    if (activeFilter === 'review') return categorizedClauses.neutral;
    return clauses || [];
  }, [activeFilter, clauses, categorizedClauses]);

  const toggleCardExpansion = (index) => {
    setExpandedCards(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getStatusBadge = (clause) => {
    if (clause.prediction?.toLowerCase() === 'entailment' || clause.status === '🟢 Compliant') {
      return { type: 'entailment', label: 'ENTAILMENT', color: '#10b981' };
    }
    if (clause.prediction?.toLowerCase() === 'contradiction' || clause.status === '🔴 Violation') {
      return { type: 'contradiction', label: 'CONTRADICTION', color: '#ef4444' };
    }
    return { type: 'neutral', label: 'NEUTRAL', color: '#f59e0b' };
  };

  const getConfidenceColor = (confidence, statusType) => {
    if (statusType === 'entailment') return '#10b981';
    if (statusType === 'contradiction') return '#f97316';
    return '#f59e0b';
  };

  // Handle stat card clicks
  const handleStatClick = (filter) => {
    setActiveFilter(filter);
    if (clauseDetailsRef.current) {
      clauseDetailsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Generate TXT Report
  const generateTXTReport = () => {
    const reportContent = `
LEGAL COMPLIANCE ANALYSIS REPORT
================================
Generated: ${new Date().toLocaleString()}
Document Type: ${currentDocType.name}
Domain: ${domain?.toUpperCase() || 'GENERAL'}

EXECUTIVE SUMMARY
-----------------
Total Clauses Analyzed: ${stats.total}
Compliant (Entailment): ${stats.compliant} (${stats.compliantPercent}%)
Non-Compliant (Contradiction): ${stats.nonCompliant} (${stats.nonCompliantPercent}%)
Missing Mandatory Clauses: ${mandatoryAnalysis.missing.length}

COMPLIANCE STATUS: ${stats.nonCompliant > 0 ? 'ISSUES FOUND' : 'COMPLIANT'}

DETAILED CLAUSE ANALYSIS
------------------------
${clauses?.map((clause, index) => {
  const status = getStatusBadge(clause);
  return `
[${index + 1}] ${status.label}
Clause: ${clause.clause}
Status: ${status.type === 'entailment' ? 'LEGAL' : 'ILLEGAL'}
Confidence: ${(clause.confidence || 0).toFixed(1)}%
Law Reference: ${clause.law_reference || clause.violated_act || 'N/A'}
${clause.matched_rule ? `Applicable Law: ${clause.matched_rule}` : ''}
---
`;
}).join('\n')}

MANDATORY CLAUSES CHECK
-----------------------
Present Clauses (${mandatoryAnalysis.present.length}):
${mandatoryAnalysis.present.map(c => `  ✓ ${c.name}`).join('\n') || '  None found'}

Missing Clauses (${mandatoryAnalysis.missing.length}):
${mandatoryAnalysis.missing.map(c => `  ✗ ${c.name} - ${c.description}`).join('\n') || '  All mandatory clauses present'}

RECOMMENDATIONS
---------------
${mandatoryAnalysis.missing.length > 0 
  ? `Your document is missing ${mandatoryAnalysis.missing.length} mandatory clause(s). Consider adding these clauses to ensure full legal compliance under Sri Lankan law.`
  : 'All mandatory clauses are present in this document.'}

${stats.nonCompliant > 0 
  ? `\n${stats.nonCompliant} clause(s) were identified as potentially non-compliant and require legal review.`
  : ''}

---
Report generated by Legal Compliance Analyzer
Powered by Legal-BERT NLI & Advanced AI
    `;

    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compliance_report_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Generate Colorful PDF Report
  const generatePDFReport = () => {
    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Legal Compliance Report</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }
    .container { max-width: 900px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 16px; margin-bottom: 30px; text-align: center; }
    .header h1 { font-size: 28px; margin-bottom: 10px; }
    .header p { opacity: 0.9; font-size: 14px; }
    .badge { display: inline-block; padding: 6px 16px; background: rgba(255,255,255,0.2); border-radius: 20px; font-size: 12px; margin-top: 15px; }
    .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
    .summary-card { background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-top: 4px solid; }
    .summary-card.total { border-color: #3b82f6; }
    .summary-card.compliant { border-color: #10b981; }
    .summary-card.non-compliant { border-color: #ef4444; }
    .summary-card.missing { border-color: #8b5cf6; }
    .card-value { font-size: 32px; font-weight: 700; }
    .summary-card.total .card-value { color: #3b82f6; }
    .summary-card.compliant .card-value { color: #10b981; }
    .summary-card.non-compliant .card-value { color: #ef4444; }
    .summary-card.missing .card-value { color: #8b5cf6; }
    .card-label { font-size: 12px; color: #64748b; margin-top: 5px; }
    .section { background: white; border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .section-title { font-size: 18px; color: #1e293b; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
    .clause-item { padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 4px solid; }
    .clause-item.entailment { background: linear-gradient(to right, #f0fdf4, #ffffff); border-color: #10b981; }
    .clause-item.contradiction { background: linear-gradient(to right, #fef2f2, #ffffff); border-color: #ef4444; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; }
    .status-badge.entailment { background: #dcfce7; color: #166534; }
    .status-badge.contradiction { background: #fee2e2; color: #991b1b; }
    .clause-text { font-size: 14px; color: #475569; margin: 10px 0; font-style: italic; }
    .clause-meta { font-size: 12px; color: #64748b; display: flex; gap: 20px; }
    .mandatory-item { display: flex; align-items: center; gap: 10px; padding: 10px 15px; border-radius: 8px; margin-bottom: 8px; }
    .mandatory-item.present { background: #f0fdf4; }
    .mandatory-item.missing { background: #fef2f2; }
    .check-icon { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; }
    .check-icon.present { background: #10b981; color: white; }
    .check-icon.missing { background: #ef4444; color: white; }
    .footer { text-align: center; padding: 20px; color: #64748b; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 30px; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚖️ Legal Compliance Analysis Report</h1>
      <p>Generated on ${new Date().toLocaleString()}</p>
      <div class="badge">${currentDocType.icon} ${currentDocType.name}</div>
    </div>
    
    <div class="summary-grid">
      <div class="summary-card total">
        <div class="card-value">${stats.total}</div>
        <div class="card-label">Total Clauses</div>
      </div>
      <div class="summary-card compliant">
        <div class="card-value">${stats.compliant}</div>
        <div class="card-label">Compliant</div>
      </div>
      <div class="summary-card non-compliant">
        <div class="card-value">${stats.nonCompliant}</div>
        <div class="card-label">Non-Compliant</div>
      </div>
      <div class="summary-card missing">
        <div class="card-value">${mandatoryAnalysis.missing.length}</div>
        <div class="card-label">Missing Clauses</div>
      </div>
    </div>
    
    <div class="section">
      <div class="section-title">📝 Detailed Clause Analysis</div>
      ${clauses?.map((clause, index) => {
        const status = getStatusBadge(clause);
        return `
        <div class="clause-item ${status.type}">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600; color: #374151;">#${index + 1}</span>
            <span class="status-badge ${status.type}">${status.label}</span>
          </div>
          <p class="clause-text">"${clause.clause?.substring(0, 200)}${clause.clause?.length > 200 ? '...' : ''}"</p>
          <div class="clause-meta">
            <span>📊 Confidence: ${(clause.confidence || 0).toFixed(1)}%</span>
            <span>⚖️ ${clause.law_reference || clause.violated_act || 'N/A'}</span>
          </div>
        </div>
        `;
      }).join('')}
    </div>
    
    <div class="section">
      <div class="section-title">📋 Mandatory Clauses Check</div>
      <h4 style="color: #10b981; margin-bottom: 10px;">✅ Present Clauses (${mandatoryAnalysis.present.length})</h4>
      ${mandatoryAnalysis.present.map(c => `
        <div class="mandatory-item present">
          <div class="check-icon present">✓</div>
          <span>${c.name}</span>
        </div>
      `).join('')}
      
      ${mandatoryAnalysis.missing.length > 0 ? `
        <h4 style="color: #ef4444; margin: 20px 0 10px;">❌ Missing Clauses (${mandatoryAnalysis.missing.length})</h4>
        ${mandatoryAnalysis.missing.map(c => `
          <div class="mandatory-item missing">
            <div class="check-icon missing">✗</div>
            <span>${c.name}</span>
          </div>
        `).join('')}
      ` : ''}
    </div>
    
    <div class="footer">
      <p>Report generated by Legal Compliance Analyzer</p>
      <p>Powered by Legal-BERT NLI & Advanced AI</p>
    </div>
  </div>
</body>
</html>
    `;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.onload = function() {
      printWindow.print();
    };
  };

  // Export as JSON
  const exportJSON = () => {
    const reportData = {
      generated: new Date().toISOString(),
      documentType: currentDocType.name,
      domain: domain,
      summary: {
        total: stats.total,
        compliant: stats.compliant,
        nonCompliant: stats.nonCompliant,
        needsReview: stats.needsReview,
        missingMandatory: mandatoryAnalysis.missing.length
      },
      clauses: clauses?.map(clause => ({
        text: clause.clause,
        prediction: clause.prediction,
        confidence: clause.confidence,
        lawReference: clause.law_reference || clause.violated_act,
        matchedRule: clause.matched_rule
      })),
      mandatoryClauses: {
        present: mandatoryAnalysis.present.map(c => c.name),
        missing: mandatoryAnalysis.missing.map(c => c.name)
      }
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compliance_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="result-page">
      {/* Page Header with Navigation */}
      <div className="page-header">
        <div className="header-left">
          <button className="back-btn" onClick={onBack}>
            <span className="back-arrow">←</span>
            <span>Analyze New Document</span>
          </button>
        </div>
        <div className="header-right">
          <div className="export-dropdown">
            <button 
              className="export-btn"
              onClick={() => setShowExportMenu(!showExportMenu)}
            >
              <span className="btn-icon">📥</span>
              <span>Download Report</span>
              <span className="dropdown-arrow">▼</span>
            </button>
            {showExportMenu && (
              <div className="export-menu">
                <button onClick={() => { generateTXTReport(); setShowExportMenu(false); }}>
                  <span>📄</span> Download as TXT
                </button>
                <button onClick={() => { generatePDFReport(); setShowExportMenu(false); }}>
                  <span>📕</span> Download as PDF
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Results Header Card */}
      <div className="results-hero">
        <div className="hero-content">
          <div className="hero-left">
            <div className="domain-badge-large">
              <span className="domain-icon">{currentDocType.icon}</span>
              <span>{currentDocType.name}</span>
            </div>
            <h1 className="results-title">Compliance Analysis Complete</h1>
            <p className="results-subtitle">
              Your document has been analyzed against Sri Lankan legal requirements
            </p>
          </div>
          <div className="hero-right">
            <div className="compliance-score success">
              <div className="score-meter">
                <svg viewBox="0 0 100 100">
                  <circle className="meter-bg" cx="50" cy="50" r="40" />
                  <circle 
                    className="meter-fill"
                    cx="50" cy="50" r="40"
                    style={{
                      strokeDasharray: `${stats.compliantPercent * 2.51} 251`,
                      stroke: '#f59e0b'
                    }}
                  />
                </svg>
                <div className="meter-value">
                  <span className="score-value">{stats.compliantPercent}%</span>
                  <span className="score-label">Compliant</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Statistics - Clickable Cards */}
      <div className="summary-section">
        <h2 className="section-heading">
          <span className="heading-icon">📈</span>
          Analysis Summary
        </h2>
        
        <div className="summary-grid">
          <div 
            className={`summary-card total ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => handleStatClick('all')}
          >
            <div className="card-icon">📋</div>
            <div className="card-content">
              <span className="card-value">{stats.total}</span>
              <span className="card-label">Total Clauses</span>
            </div>
            <div className="card-action">View All →</div>
          </div>

          <div 
            className={`summary-card compliant ${activeFilter === 'compliant' ? 'active' : ''}`}
            onClick={() => handleStatClick('compliant')}
          >
            <div className="card-icon">✅</div>
            <div className="card-content">
              <span className="card-value">{stats.compliant}</span>
              <span className="card-label">Compliant</span>
              <span className="card-percent">{stats.compliantPercent}%</span>
            </div>
            <div className="card-action">View Details →</div>
          </div>

          <div 
            className={`summary-card non-compliant ${activeFilter === 'non-compliant' ? 'active' : ''}`}
            onClick={() => handleStatClick('non-compliant')}
          >
            <div className="card-icon">❌</div>
            <div className="card-content">
              <span className="card-value">{stats.nonCompliant}</span>
              <span className="card-label">Non-Compliant</span>
              <span className="card-percent">{stats.nonCompliantPercent}%</span>
            </div>
            <div className="card-action">View Issues →</div>
          </div>

          <div 
            className="summary-card missing"
            onClick={onViewMandatory}
          >
            <div className="card-icon">📝</div>
            <div className="card-content">
              <span className="card-value">{mandatoryAnalysis.missing.length}</span>
              <span className="card-label">Missing Clauses</span>
            </div>
            <div className="card-action">View Missing →</div>
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="quick-nav-section">
        <div className="quick-nav-card" onClick={onViewMandatory}>
          <div className="nav-card-icon">📜</div>
          <div className="nav-card-content">
            <h3>Mandatory Clauses</h3>
            <p>View required clauses and missing items</p>
          </div>
          <div className="nav-card-badge">
            <span className="present">{mandatoryAnalysis.present.length} Present</span>
            <span className="missing">{mandatoryAnalysis.missing.length} Missing</span>
          </div>
          <span className="nav-arrow">→</span>
        </div>

        <div className="quick-nav-card" onClick={onViewActs}>
          <div className="nav-card-icon">📚</div>
          <div className="nav-card-content">
            <h3>Download Acts</h3>
            <p>Access official Sri Lankan legislation PDFs</p>
          </div>
          <span className="nav-arrow">→</span>
        </div>
      </div>

      {/* Clause Details Section */}
      <div className="clause-details-section" ref={clauseDetailsRef}>
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">📝</span>
            <h2>Detailed Clause Analysis</h2>
          </div>
          
          {/* Filter Tabs */}
          <div className="filter-tabs">
            <button 
              className={`filter-tab ${activeFilter === 'all' ? 'active' : ''}`}
              onClick={() => setActiveFilter('all')}
            >
              All ({clauses?.length || 0})
            </button>
            <button 
              className={`filter-tab compliant ${activeFilter === 'compliant' ? 'active' : ''}`}
              onClick={() => setActiveFilter('compliant')}
            >
              ✅ Entailment ({stats.compliant})
            </button>
            <button 
              className={`filter-tab non-compliant ${activeFilter === 'non-compliant' ? 'active' : ''}`}
              onClick={() => setActiveFilter('non-compliant')}
            >
              ❌ Contradiction ({stats.nonCompliant})
            </button>
          </div>
        </div>

        {/* Active Filter Indicator */}
        {activeFilter !== 'all' && activeFilter !== 'review' && (
          <div className={`filter-indicator ${activeFilter}`}>
            <span className="filter-icon">
              {activeFilter === 'compliant' ? '✅' : '❌'}
            </span>
            <span>Showing {filteredClauses.length} {activeFilter === 'compliant' ? 'compliant (entailment)' : 'non-compliant (contradiction)'} clauses</span>
            <button className="clear-filter" onClick={() => setActiveFilter('all')}>Clear Filter ✕</button>
          </div>
        )}

        {/* Clause Cards */}
        <div className="clause-cards">
          {filteredClauses.map((clause, index) => {
            const status = getStatusBadge(clause);
            const confidence = clause.confidence || 0;
            const isExpanded = expandedCards[index];
            
            return (
              <div 
                key={index} 
                className={`clause-card ${status.type} ${isExpanded ? 'expanded' : 'collapsed'}`}
              >
                {/* Card Header - Always Visible */}
                <div className="card-header clickable" onClick={() => toggleCardExpansion(index)}>
                  <div className="card-number">#{index + 1}</div>
                  <div className={`status-badge ${status.type}`}>
                    <span className="status-dot"></span>
                    <span>{status.label}</span>
                  </div>
                  <div className="expand-indicator">
                    {isExpanded ? '▲' : '▼'}
                  </div>
                </div>

                {/* Clause Text - Always Visible */}
                <div className="clause-content">
                  <div className="clause-label">
                    <span className="label-icon">📄</span>
                    <span>Contract Clause</span>
                  </div>
                  <p className="clause-text">
                    "{clause.clause}"
                  </p>
                </div>

                {/* Collapsible Details Section */}
                {isExpanded && (
                  <>
                    {/* Details Grid */}
                    <div className="clause-details-grid">
                  <div className="detail-item">
                    <div className="detail-label">
                      <span className="detail-icon">⚖️</span>
                      LAW REFERENCE
                    </div>
                    <div className="detail-value">
                      {clause.law_reference ? (
                        clause.law_reference
                      ) : clause.violated_act ? (
                        `${clause.violated_act}${clause.section ? ` Section ${clause.section}` : ''}`
                      ) : (
                        'No specific law reference'
                      )}
                    </div>
                  </div>

                  <div className="detail-item">
                    <div className="detail-label">
                      <span className="detail-icon">✓</span>
                      STATUS
                    </div>
                    <div className={`detail-value status ${status.type}`}>
                      <span className="status-indicator"></span>
                      {status.type === 'entailment' ? 'LEGAL' : 
                       status.type === 'contradiction' ? 'ILLEGAL' : 'NEEDS REVIEW'}
                    </div>
                  </div>

                  <div className="detail-item confidence">
                    <div className="detail-label">
                      <span className="detail-icon">📊</span>
                      CONFIDENCE SCORE
                    </div>
                    <div className="confidence-display">
                      <div className="confidence-bar">
                        <div 
                          className="confidence-fill"
                          style={{ 
                            width: `${confidence}%`,
                            backgroundColor: getConfidenceColor(confidence, status.type)
                          }}
                        >
                          <span className="confidence-label">{confidence.toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Matched Rule Display */}
                {clause.matched_rule && (
                  <div className="matched-rule-section">
                    <div className="matched-rule-label">
                      <span className="rule-icon">📖</span>
                      APPLICABLE LAW PROVISION
                    </div>
                    <p className="matched-rule-text">
                      {clause.matched_rule}
                    </p>
                  </div>
                )}

                {/* Analysis & Recommendation */}
                <div className="analysis-section">
                  <div className="analysis-label">
                    <span className="analysis-icon">💡</span>
                    ANALYSIS & RECOMMENDATION
                  </div>
                  <p className="analysis-text">
                    {clause.recommendation ? (
                      clause.recommendation
                    ) : (
                      <>
                        Model predicts {status.label} with confidence {confidence.toFixed(1)}%
                        {status.type === 'contradiction' && 
                          `. This clause may violate ${clause.violated_act || 'relevant regulations'}${clause.section ? ` Section ${clause.section}` : ''}. Legal review required.`}
                        {status.type === 'entailment' && 
                          '. This clause appears to comply with applicable laws.'}
                        {status.type === 'neutral' && 
                          '. This clause requires further human review for compliance determination.'}
                      </>
                    )}
                  </p>
                </div>
                  </>
                )}
              </div>
            );
          })}
        </div>

        {/* No Results */}
        {(!filteredClauses || filteredClauses.length === 0) && (
          <div className="no-results">
            <span className="no-results-icon">📭</span>
            <h3>No clauses found</h3>
            <p>No clauses matching the selected filter were found in the document.</p>
            <button className="reset-btn" onClick={() => setActiveFilter('all')}>
              View All Clauses
            </button>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button className="action-btn secondary" onClick={onBack}>
          <span className="btn-icon">📤</span>
          Analyze New Document
        </button>
        <button className="action-btn primary" onClick={generatePDFReport}>
          <span className="btn-icon">📥</span>
          Download Full Report
        </button>
      </div>
    </div>
  );
}

export default ResultPage;
