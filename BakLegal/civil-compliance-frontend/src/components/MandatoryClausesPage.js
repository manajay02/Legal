import React, { useMemo } from 'react';
import '../styles/MandatoryClausesPage.css';

function MandatoryClausesPage({ results, onBack, onReAnalyze }) {
  const { domain, clauses, present_mandatory, missing_mandatory, document_type } = results;

  // Mandatory clauses definition for different document types
  const mandatoryClausesByType = {
    employment: {
      name: 'Employment Contract',
      icon: '👔',
      description: 'Mandatory clauses required under Sri Lankan Employment Law',
      acts: ['Shop and Office Employees Act', 'EPF Act', 'ETF Act', 'Maternity Benefits Ordinance'],
      clauses: [
        { id: 'salary', name: 'Salary/Compensation', description: 'Monthly salary, payment schedule, and method', legal: 'Shop and Office Employees Act' },
        { id: 'working_hours', name: 'Working Hours', description: 'Daily and weekly working hours as per Shop and Office Act', legal: 'Section 3, Shop and Office Act' },
        { id: 'epf', name: 'EPF Contributions', description: 'Employees\' Provident Fund contributions (8% employee, 12% employer)', legal: 'EPF Act No. 15 of 1958' },
        { id: 'etf', name: 'ETF Contributions', description: 'Employees\' Trust Fund contributions (3% employer)', legal: 'ETF Act No. 46 of 1980' },
        { id: 'leave_policy', name: 'Leave Policy', description: 'Annual leave, sick leave, and casual leave entitlements', legal: 'Shop and Office Employees Act' },
        { id: 'termination', name: 'Termination Clause', description: 'Notice period, termination conditions, and severance', legal: 'Industrial Disputes Act' },
        { id: 'probation', name: 'Probation Period', description: 'Duration and conditions of probationary period', legal: 'Common Law' },
        { id: 'job_description', name: 'Job Description', description: 'Duties and responsibilities of the employee', legal: 'Best Practice' },
        { id: 'maternity', name: 'Maternity Benefits', description: 'Maternity leave as per Maternity Benefits Ordinance', legal: 'Maternity Benefits Ordinance No. 32 of 1939' },
        { id: 'overtime', name: 'Overtime Provisions', description: 'Overtime rates and conditions', legal: 'Shop and Office Employees Act' },
        { id: 'gratuity', name: 'Gratuity Entitlement', description: 'Gratuity payment upon completion of service', legal: 'Gratuity Act No. 12 of 1983' },
        { id: 'notice_period', name: 'Notice Period & Severance', description: 'Required notice period for termination', legal: 'Industrial Disputes Act' },
        { id: 'minimum_wage', name: 'Minimum Wages', description: 'Compliance with minimum wage requirements', legal: 'Wages Boards Ordinance' },
        { id: 'employee_identification', name: 'Employee Name & Job Title', description: 'Clear identification of employee and position', legal: 'Best Practice' },
      ]
    },
    rental: {
      name: 'Rental Agreement',
      icon: '🏠',
      description: 'Required clauses for valid rental agreements under Sri Lankan Law',
      acts: ['Rent Act No. 7 of 1972', 'Registration of Documents Ordinance'],
      clauses: [
        { id: 'parties', name: 'Parties\' Names & Addresses', description: 'Full names and addresses of landlord and tenant', legal: 'Rent Act' },
        { id: 'property_description', name: 'Description of Property', description: 'Clear description of the rental property', legal: 'Rent Act' },
        { id: 'rent_amount', name: 'Rent Amount & Payment Method', description: 'Monthly rent and payment terms', legal: 'Rent Act Section 5' },
        { id: 'duration', name: 'Duration of Tenancy', description: 'Start and end date of tenancy period', legal: 'Rent Act' },
        { id: 'security_deposit', name: 'Security Deposit', description: 'Deposit amount and refund conditions', legal: 'Common Law' },
        { id: 'termination_notice', name: 'Termination / Notice Period', description: 'Notice period for ending tenancy', legal: 'Rent Act Section 22' },
        { id: 'rights_obligations', name: 'Rights & Obligations', description: 'Rights and duties of tenant and landlord', legal: 'Rent Act' },
        { id: 'registration', name: 'Registration of Agreement', description: 'Registration of Documents Ordinance compliance', legal: 'Registration of Documents Ordinance' },
      ]
    },
    finance_leasing: {
      name: 'Finance Leasing Agreement',
      icon: '🚗',
      description: 'Mandatory provisions under Finance Leasing Act',
      acts: ['Finance Leasing Act No. 56 of 2000', 'Consumer Affairs Authority Act'],
      clauses: [
        { id: 'lease_rental', name: 'Lease Rental Amount', description: 'Monthly lease rental payment amount', legal: 'Finance Leasing Act Section 6' },
        { id: 'lease_term', name: 'Lease Term/Period', description: 'Duration of the lease', legal: 'Finance Leasing Act' },
        { id: 'asset_description', name: 'Equipment/Vehicle Description', description: 'Detailed description of the leased asset', legal: 'Finance Leasing Act Section 5' },
        { id: 'insurance', name: 'Insurance Requirements', description: 'Insurance obligations for the leased asset', legal: 'Finance Leasing Act Section 10' },
        { id: 'repossession', name: 'Repossession Rights', description: 'Conditions under which asset can be repossessed', legal: 'Finance Leasing Act Section 12' },
        { id: 'ownership_transfer', name: 'Ownership Transfer', description: 'Terms for transfer of ownership at end of lease', legal: 'Finance Leasing Act Section 8' },
      ]
    },
    consumer: {
      name: 'Loan/Credit Agreement',
      icon: '💰',
      description: 'Required clauses under Consumer Credit and Banking Law',
      acts: ['Consumer Affairs Authority Act', 'Banking Act', 'Finance Business Act'],
      clauses: [
        { id: 'loan_amount', name: 'Loan/Principal Amount', description: 'The principal loan amount clearly stated', legal: 'Banking Act' },
        { id: 'interest_rate', name: 'Interest Rate & Calculation', description: 'Interest rate and how it is calculated', legal: 'Consumer Affairs Authority Act' },
        { id: 'repayment_schedule', name: 'Repayment Schedule', description: 'Installments, due dates, and repayment terms', legal: 'Consumer Credit Regulations' },
        { id: 'borrower_rights', name: 'Borrower Rights', description: 'Early settlement rights, complaint procedures', legal: 'Consumer Affairs Authority Act' },
        { id: 'late_payment_penalty', name: 'Late Payment Penalty', description: 'Reasonable and legally permitted late fees', legal: 'Consumer Protection Guidelines' },
        { id: 'debt_recovery', name: 'Debt Recovery Procedures', description: 'Collection and recovery procedures', legal: 'Debt Recovery Act' },
      ]
    },
    partnership: {
      name: 'Partnership Agreement',
      icon: '🤝',
      description: 'Essential clauses under Partnership Ordinance',
      acts: ['Partnership Ordinance No. 21 of 1866'],
      clauses: [
        { id: 'partners', name: 'Partners\' Names & Capital', description: 'Names of all partners and their capital contributions', legal: 'Partnership Ordinance Section 5' },
        { id: 'profit_sharing', name: 'Profit/Loss Sharing Ratio', description: 'How profits and losses are divided', legal: 'Partnership Ordinance Section 24' },
        { id: 'duties', name: 'Duties & Responsibilities', description: 'Roles and responsibilities of each partner', legal: 'Partnership Ordinance' },
        { id: 'decision_making', name: 'Decision-Making Authority', description: 'How decisions are made in the partnership', legal: 'Partnership Ordinance Section 24(8)' },
        { id: 'partnership_duration', name: 'Duration of Partnership', description: 'How long the partnership will last', legal: 'Partnership Ordinance' },
        { id: 'dissolution', name: 'Termination/Dissolution Terms', description: 'How the partnership can be ended', legal: 'Partnership Ordinance Section 32-44' },
      ]
    },
    general: {
      name: 'Legal Document',
      icon: '📄',
      description: 'Basic requirements for legal documents',
      acts: ['Contract Law'],
      clauses: [
        { id: 'parties', name: 'Parties Identification', description: 'Names and details of all parties', legal: 'Contract Law' },
        { id: 'terms', name: 'Terms & Conditions', description: 'Main terms of the agreement', legal: 'Contract Law' },
        { id: 'signatures', name: 'Signatures', description: 'Signature requirements', legal: 'Contract Law' },
      ]
    },
    other: {
      name: 'Legal Document',
      icon: '📄',
      description: 'Standard legal document requirements',
      acts: ['Contract Law'],
      clauses: [
        { id: 'parties', name: 'Parties Involved', description: 'Names and details of parties', legal: 'Contract Law' },
        { id: 'terms', name: 'Terms & Conditions', description: 'Main terms of agreement', legal: 'Contract Law' },
        { id: 'signatures', name: 'Signatures', description: 'Signature requirements', legal: 'Contract Law' },
      ]
    }
  };

  const docType = document_type || domain || 'other';
  const currentDocType = mandatoryClausesByType[docType] || mandatoryClausesByType.other;

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
            confidence: backendClause.confidence,
            legal: backendClause.legal_basis || 'N/A'
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
            rule: backendClause.rule,
            legal: backendClause.legal_basis || 'N/A'
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

  const compliancePercent = currentDocType.clauses.length > 0 
    ? ((mandatoryAnalysis.present.length / currentDocType.clauses.length) * 100).toFixed(0)
    : 0;

  return (
    <div className="mandatory-page">
      {/* Page Header */}
      <div className="page-header">
        <div className="header-left">
          <button className="back-btn" onClick={onBack}>
            <span className="back-arrow">←</span>
            <span>Back to Results</span>
          </button>
        </div>
        <div className="header-right">
          <button className="reanalyze-btn" onClick={onReAnalyze}>
            <span className="btn-icon">📤</span>
            <span>Analyze New Document</span>
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="mandatory-hero">
        <div className="hero-content">
          <div className="hero-left">
            <div className="document-type-badge">
              <span className="type-icon">{currentDocType.icon}</span>
              <span>{currentDocType.name}</span>
            </div>
            <h1 className="page-title">Mandatory Clauses Checker</h1>
            <p className="page-subtitle">{currentDocType.description}</p>
          </div>
          <div className="hero-right">
            <div className="compliance-meter">
              <div className="meter-circle">
                <svg viewBox="0 0 100 100">
                  <circle className="meter-bg" cx="50" cy="50" r="40" />
                  <circle 
                    className="meter-fill"
                    cx="50" cy="50" r="40"
                    style={{
                      strokeDasharray: `${compliancePercent * 2.51} 251`,
                      stroke: compliancePercent >= 80 ? '#10b981' : compliancePercent >= 50 ? '#f59e0b' : '#ef4444'
                    }}
                  />
                </svg>
                <div className="meter-value">
                  <span className="value">{compliancePercent}%</span>
                  <span className="label">Complete</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs - Same Style as ResultPage */}
      <div className="filter-tabs-container">
        <div className="filter-tabs">
          <button className="filter-tab" onClick={() => document.getElementById('checklist-section').scrollIntoView({ behavior: 'instant' })}>
            All ({currentDocType.clauses.length})
          </button>
          <button className="filter-tab present" onClick={() => document.getElementById('present-section').scrollIntoView({ behavior: 'instant' })}>
            <span className="tab-check">✅</span>
            Present ({mandatoryAnalysis.present.length})
          </button>
          <button className="filter-tab missing" onClick={() => document.getElementById('missing-section').scrollIntoView({ behavior: 'instant' })}>
            <span className="tab-x">❌</span>
            Missing ({mandatoryAnalysis.missing.length})
          </button>
        </div>
      </div>

      {/* Clauses Grid */}
      <div className="clauses-container">
        {/* All Required Clauses Checklist */}
        <div id="checklist-section" className="clauses-section checklist-section">
          <div className="section-header with-stats">
            <div className="header-title">
              <span className="section-icon">📜</span>
              <h2>Required Clauses Checklist</h2>
            </div>
            <div className="header-stats">
              <div className="mini-stat total">
                <span className="mini-value">{currentDocType.clauses.length}</span>
                <span className="mini-label">Total Required</span>
              </div>
              <div className="mini-stat present">
                <span className="mini-value">{mandatoryAnalysis.present.length}</span>
                <span className="mini-label">Present</span>
              </div>
              <div className="mini-stat missing">
                <span className="mini-value">{mandatoryAnalysis.missing.length}</span>
                <span className="mini-label">Missing</span>
              </div>
            </div>
          </div>
          <div className="checklist-grid">
            {currentDocType.clauses.map((clause, index) => {
              const isPresent = mandatoryAnalysis.present.some(p => p.id === clause.id);
              return (
                <div 
                  key={clause.id} 
                  className={`checklist-card ${isPresent ? 'present' : 'missing'}`}
                >
                  <div className="card-status">
                    <span className="status-icon">{isPresent ? '✅' : '❌'}</span>
                    <span className="status-text">{isPresent ? 'Present' : 'Missing'}</span>
                  </div>
                  <div className="card-content">
                    <h4 className="clause-name">{clause.name}</h4>
                    <p className="clause-description">{clause.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Missing Clauses Section */}
        {mandatoryAnalysis.missing.length > 0 && (
          <div id="missing-section" className="clauses-section missing-section">
            <div className="section-header warning">
              <span className="section-icon">⚠️</span>
              <h2>Missing Mandatory Clauses</h2>
              <span className="section-badge">{mandatoryAnalysis.missing.length} Issues</span>
            </div>
            <div className="missing-alert">
              <div className="alert-icon">💡</div>
              <div className="alert-content">
                <h4>Action Required</h4>
                <p>
                  The following {mandatoryAnalysis.missing.length} mandatory clause(s) are missing from your document. 
                  Adding these clauses is recommended to ensure full legal compliance under Sri Lankan law.
                </p>
              </div>
            </div>
            <div className="missing-list">
              {mandatoryAnalysis.missing.map((clause, index) => (
                <div key={clause.id} className="missing-card">
                  <div className="card-number">{index + 1}</div>
                  <div className="card-content">
                    <h4 className="clause-name">
                      <span className="missing-icon">❌</span>
                      {clause.name}
                    </h4>
                    <p className="clause-description">{clause.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Present Clauses Section */}
        {mandatoryAnalysis.present.length > 0 && (
          <div id="present-section" className="clauses-section present-section">
            <div className="section-header success">
              <span className="section-icon">✅</span>
              <h2>Present Mandatory Clauses</h2>
              <span className="section-badge success">{mandatoryAnalysis.present.length} Found</span>
            </div>
            <div className="present-list">
              {mandatoryAnalysis.present.map((clause, index) => (
                <div key={clause.id} className="present-card">
                  <div className="card-check">✓</div>
                  <div className="card-content">
                    <h4 className="clause-name">{clause.name}</h4>
                    <p className="clause-description">{clause.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Present Message */}
        {mandatoryAnalysis.missing.length === 0 && (
          <div className="all-present-message">
            <div className="message-icon">🎉</div>
            <h3>Congratulations!</h3>
            <p>All mandatory clauses are present in your document. Your {currentDocType.name} appears to be complete.</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button className="action-btn secondary" onClick={onBack}>
          <span className="btn-icon">←</span>
          Back to Results
        </button>
        <button className="action-btn primary" onClick={onReAnalyze}>
          <span className="btn-icon">📤</span>
          Analyze Another Document
        </button>
      </div>
    </div>
  );
}

export default MandatoryClausesPage;
