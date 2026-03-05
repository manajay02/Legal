import React, { useState, useMemo } from 'react';
import '../styles/ResultPage.css';

function ResultPage({ results, onBack }) {
  const { domain, clauses, present_mandatory, missing_mandatory, document_type } = results;
  const [activeFilter, setActiveFilter] = useState('all');
  const [expandedCards, setExpandedCards] = useState({});

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
        { id: 'assignment_of_debt', name: 'Assignment of Debt', description: 'Terms for transferring debt to third parties' },
        { id: 'written_modifications', name: 'Written Modifications Only', description: 'Agreement can only be modified in writing' },
        { id: 'electronic_validity', name: 'Electronic Communications', description: 'Validity of electronic signatures and communications' },
        { id: 'limitation_of_liability', name: 'Limitation of Liability', description: 'Cannot waive statutory obligations' },
        { id: 'signatures', name: 'Signatures of Parties', description: 'Both parties must sign the agreement' },
        { id: 'sale_delivery_terms', name: 'Sale/Delivery of Goods Terms', description: 'Terms for sale and delivery of goods' },
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
        { id: 'partner_signatures', name: 'Signatures of All Partners', description: 'All partners must sign the agreement' },
      ]
    },
    sales: {
      name: 'Sales Contract',
      icon: '📦',
      clauses: [
        { id: 'goods_description', name: 'Goods Description', description: 'Detailed description of items being sold' },
        { id: 'price', name: 'Price Terms', description: 'Total price and payment terms' },
        { id: 'delivery', name: 'Delivery Terms', description: 'Delivery date, location, and method' },
        { id: 'warranty', name: 'Warranty', description: 'Warranty period and coverage' },
        { id: 'title_transfer', name: 'Title Transfer', description: 'When ownership transfers to buyer' },
        { id: 'returns', name: 'Return Policy', description: 'Conditions for returns and refunds' },
      ]
    },
    service: {
      name: 'Service Agreement',
      icon: '🛠️',
      clauses: [
        { id: 'service_description', name: 'Service Description', description: 'Detailed scope of services' },
        { id: 'payment_terms', name: 'Payment Terms', description: 'Fees, schedule, and method' },
        { id: 'duration', name: 'Duration', description: 'Start and end date of service' },
        { id: 'deliverables', name: 'Deliverables', description: 'Expected outputs and milestones' },
        { id: 'liability', name: 'Liability', description: 'Limitation of liability' },
        { id: 'termination', name: 'Termination', description: 'How either party can end agreement' },
      ]
    },
    nda: {
      name: 'Non-Disclosure Agreement',
      icon: '🔒',
      clauses: [
        { id: 'confidential_info', name: 'Confidential Information', description: 'Definition of what is confidential' },
        { id: 'obligations', name: 'Obligations', description: 'What recipient must do to protect info' },
        { id: 'duration', name: 'Duration', description: 'How long confidentiality lasts' },
        { id: 'exceptions', name: 'Exceptions', description: 'What is not considered confidential' },
        { id: 'remedies', name: 'Remedies', description: 'Consequences of breach' },
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

  // Get the mandatory clauses for current document type
  // Use document_type first, fallback to domain, then to 'other'
  const docType = document_type || domain || 'other';
  const currentDocType = mandatoryClausesByType[docType] || mandatoryClausesByType.other;
  
  // Debug logging (can be removed in production)
  console.log('Document Type:', document_type, '| Domain:', domain, '| Using:', docType);

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

  // Determine which mandatory clauses are present vs missing
  // Uses backend's present_mandatory/missing_mandatory arrays (Hybrid: Rule-Based + NLI)
  const mandatoryAnalysis = useMemo(() => {
    const present = [];
    const missing = [];
    
    // If backend provides present_mandatory array, use it directly
    if (present_mandatory && present_mandatory.length > 0) {
      // Use backend data directly - map to frontend clause definitions for display
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
          // Backend has clause not in frontend definition - add it
          present.push({
            id: backendClause.id,
            name: backendClause.clause,
            description: backendClause.legal_basis || '',
            confidence: backendClause.confidence
          });
        }
      });
    }
    
    // If backend provides missing_mandatory array, use it directly
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
          // Backend has clause not in frontend definition - add it
          missing.push({
            id: backendClause.id,
            name: backendClause.clause,
            description: backendClause.legal_basis || '',
            rule: backendClause.rule
          });
        }
      });
    }
    
    // Fallback: If backend doesn't provide these arrays, use old keyword-based detection
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
    // Green for entailment, Orange for contradiction, Yellow for neutral
    if (statusType === 'entailment') return '#10b981';  // Green
    if (statusType === 'contradiction') return '#f97316';  // Orange
    return '#f59e0b';  // Yellow for neutral/needs review
  };

  return (
    <div className="result-page">
      {/* Navigation */}
      <div className="result-nav">
        <button className="back-btn" onClick={onBack}>
          <span className="back-arrow">←</span>
          <span>Analyze Another Document</span>
        </button>
      </div>

      {/* Main Results Card */}
      <div className="results-main-card">
        {/* Header */}
        <div className="results-header">
          <div className="results-title">
            <span className="title-icon">📊</span>
            <h1>Compliance Analysis Results</h1>
          </div>
          <div className="domain-badge">
            <span>Domain: {domain?.toUpperCase() || 'GENERAL'}</span>
          </div>
        </div>

        {/* Summary Section */}
        <div className="summary-section">
          <div className="summary-header">
            <span className="summary-icon">📈</span>
            <div>
              <h2>Analysis Summary</h2>
              <p>Comprehensive overview of compliance analysis</p>
            </div>
          </div>

          <div className="summary-grid">
            <div className="summary-stat">
              <div className="stat-icon">📋</div>
              <div className="stat-value total">{stats.total}</div>
              <div className="stat-label">TOTAL CLAUSES ANALYZED</div>
            </div>
            <div className="summary-stat">
              <div className="stat-icon">✅</div>
              <div className="stat-value compliant">{stats.compliant}</div>
              <div className="stat-label">COMPLIANT CLAUSES</div>
              <div className="stat-percent compliant">{stats.compliantPercent}%</div>
            </div>
            <div className="summary-stat">
              <div className="stat-icon">❌</div>
              <div className="stat-value non-compliant">{stats.nonCompliant}</div>
              <div className="stat-label">NON-COMPLIANT</div>
              <div className="stat-percent non-compliant">{stats.nonCompliantPercent}%</div>
            </div>
            <div className="summary-stat">
              <div className="stat-icon">⚠️</div>
              <div className="stat-value review">{stats.needsReview}</div>
              <div className="stat-label">REQUIRES REVIEW</div>
              <div className="stat-percent review">{stats.neutralPercent}%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Clauses Checker */}
      <div className="mandatory-checker-section">
        <div className="mandatory-header">
          <div className="mandatory-title">
            <span className="mandatory-icon">{currentDocType.icon}</span>
            <div>
              <h2>Mandatory Clauses Checker</h2>
              <p>Required clauses for {currentDocType.name} under Sri Lankan Law</p>
            </div>
          </div>
          <div className="mandatory-progress">
            <div className="progress-circle">
              <span className="progress-value">
                {mandatoryAnalysis.present.length}/{currentDocType.clauses.length}
              </span>
            </div>
            <span className="progress-label">Present</span>
          </div>
        </div>

        <div className="mandatory-grid">
          {/* Required Clauses */}
          <div className="mandatory-column required">
            <div className="column-header">
              <span className="column-icon">📜</span>
              <h3>Required Clauses for {currentDocType.name}</h3>
            </div>
            <div className="clause-checklist">
              {currentDocType.clauses.map((clause, index) => {
                const isPresent = mandatoryAnalysis.present.some(p => p.id === clause.id);
                return (
                  <div 
                    key={clause.id} 
                    className={`checklist-item ${isPresent ? 'present' : 'missing'}`}
                  >
                    <span className="check-icon">{isPresent ? '✅' : '⬜'}</span>
                    <div className="checklist-content">
                      <span className="checklist-name">{clause.name}</span>
                      <span className="checklist-desc">{clause.description}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Present & Missing Split */}
          <div className="mandatory-column status-split">
            {/* Present Clauses */}
            <div className="status-box present">
              <div className="status-box-header">
                <span className="status-icon">✅</span>
                <h4>Document Contains</h4>
                <span className="count-badge present">{mandatoryAnalysis.present.length}</span>
              </div>
              <div className="status-items">
                {mandatoryAnalysis.present.length > 0 ? (
                  mandatoryAnalysis.present.map(clause => (
                    <div key={clause.id} className="status-item present">
                      <span className="item-check">✔</span>
                      <span className="item-name">{clause.name}</span>
                    </div>
                  ))
                ) : (
                  <div className="no-items">No mandatory clauses found</div>
                )}
              </div>
            </div>

            {/* Missing Clauses */}
            <div className="status-box missing">
              <div className="status-box-header">
                <span className="status-icon">❌</span>
                <h4>Missing Clauses</h4>
                <span className="count-badge missing">{mandatoryAnalysis.missing.length}</span>
              </div>
              <div className="status-items">
                {mandatoryAnalysis.missing.length > 0 ? (
                  mandatoryAnalysis.missing.map(clause => (
                    <div key={clause.id} className="status-item missing">
                      <span className="item-check">✕</span>
                      <span className="item-name">{clause.name}</span>
                    </div>
                  ))
                ) : (
                  <div className="all-present">
                    <span>🎉</span> All mandatory clauses present!
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Missing Recommendation */}
        {mandatoryAnalysis.missing.length > 0 && (
          <div className="missing-recommendation">
            <div className="recommendation-icon">💡</div>
            <div className="recommendation-content">
              <h4>Recommendation</h4>
              <p>
                Your document is missing {mandatoryAnalysis.missing.length} mandatory clause(s) 
                that are typically required for a {currentDocType.name}. Consider adding these 
                clauses to ensure full legal compliance.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Clause Details Section */}
      <div className="clause-details-section">
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
              Compliant ({stats.compliant})
            </button>
            <button 
              className={`filter-tab non-compliant ${activeFilter === 'non-compliant' ? 'active' : ''}`}
              onClick={() => setActiveFilter('non-compliant')}
            >
              Non-Compliant ({stats.nonCompliant})
            </button>
            <button 
              className={`filter-tab review ${activeFilter === 'review' ? 'active' : ''}`}
              onClick={() => setActiveFilter('review')}
            >
              Needs Review ({stats.needsReview})
            </button>
          </div>
        </div>

        {/* Clause Cards */}
        <div className="clause-cards">
          {filteredClauses.map((clause, index) => {
            const status = getStatusBadge(clause);
            const confidence = clause.confidence || 0;
            const isExpanded = expandedCards[index];
            
            return (
              <div 
                key={index} 
                className={`clause-card ${status.type}`}
              >
                {/* Status Badge */}
                <div className="card-status-row">
                  <div className={`status-badge ${status.type}`}>
                    <span className="status-dot"></span>
                    <span>{status.label}</span>
                  </div>
                </div>

                {/* Clause Text */}
                <div className="clause-content">
                  <div className="clause-label">
                    <span className="label-icon">📄</span>
                    <span>Clause:</span>
                  </div>
                  <p className={`clause-text ${isExpanded ? 'expanded' : ''}`}>
                    {clause.clause}
                  </p>
                  {clause.clause?.length > 200 && (
                    <button 
                      className="expand-btn"
                      onClick={() => toggleCardExpansion(index)}
                    >
                      {isExpanded ? 'Show less' : 'Show more'}
                    </button>
                  )}
                </div>

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
                      <span className="confidence-value">{confidence.toFixed(1)}%</span>
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

                  <div className="detail-item">
                    <div className="detail-label">
                      <span className="detail-icon">🏷️</span>
                      CATEGORY
                    </div>
                    <div className={`detail-value category ${status.type}`}>
                      {status.type === 'entailment' ? 'Compliant' : 
                       status.type === 'contradiction' ? 'Non-Compliant' : 'Under Review'}
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
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button className="action-btn secondary" onClick={onBack}>
          <span className="btn-icon">📤</span>
          Analyze New Document
        </button>
        <button className="action-btn primary" onClick={() => window.print()}>
          <span className="btn-icon">🖨️</span>
          Print Report
        </button>
      </div>
    </div>
  );
}

export default ResultPage;
