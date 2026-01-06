import React, { useState } from 'react';
import './ArgumentScore.css';

function ArgumentScore() {
  const [argumentText, setArgumentText] = useState('');
  // eslint-disable-next-line no-unused-vars
  const [caseFile, setCaseFile] = useState(null);
  const [jurisdiction, setJurisdiction] = useState('');
  const [caseType, setCaseType] = useState('');
  const [partyRole, setPartyRole] = useState('');
  const [desiredRemedy, setDesiredRemedy] = useState('');
  const [scoreResult, setScoreResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [textFormatting, setTextFormatting] = useState({ bold: false, italic: false, underline: false });

  const handleFileChange = (e) => {
    setCaseFile(e.target.files[0]);
  };

  const handleScoreArgument = async () => {
    if (!argumentText.trim()) {
      alert('Please enter argument text');
      return;
    }

    setLoading(true);
    // Simulated API call
    setTimeout(() => {
      setScoreResult({
        overallScore: 72,
        maxScore: 100,
        strength: 'Moderate Strength',
        summary: 'The argument establishes a clear duty of care but lacks sufficient evidentiary support to conclusively prove breach.',
        markingSchema: [
          {
            criterion: 'Issue & Claim Clarity',
            weight: 20,
            score: 18,
            maxScore: 20,
            rationale: 'The claim regarding negligence is clearly stated. The cause of action is explicitly identified in the opening paragraph.'
          },
          {
            criterion: 'Facts & Chronology',
            weight: 20,
            score: 14,
            maxScore: 20,
            rationale: 'Timeline is established but gaps exist between May 1st and June 12th regarding specific maintenance actions.'
          },
          {
            criterion: 'Legal Basis & Elements',
            weight: 30,
            score: 25,
            maxScore: 30,
            rationale: 'Correctly identifies the four elements of negligence. Duty and damages are well-argued.'
          },
          {
            criterion: 'Evidence & Support',
            weight: 30,
            score: 15,
            maxScore: 30,
            rationale: 'Reliance on "absence of logs" is a negative inference. Positive evidence of disrepair is needed to strengthen the breach element.'
          }
        ],
        weaknesses: [
          {
            title: 'Missing Witness Statements',
            description: 'No references to third-party observers of the injury event'
          },
          {
            title: 'Causation Link',
            description: 'The link between the missing logs and the specific accident is inferential rather than direct.'
          },
          {
            title: 'Jurisdictional Citations',
            description: 'Lacks specific case law precedents for California premise liability in commercial zones.'
          }
        ],
        improvements: [
          {
            step: 1,
            title: 'Cite Specific Precedent',
            description: 'Add a reference to Rowland v. Christian to solidify the duty of care argument.'
          },
          {
            step: 2,
            title: 'Clarify Causation',
            description: 'Explicitly state how the maintenance failure physically caused the slip (e.g., fluid accumulation).'
          },
          {
            step: 3,
            title: 'Attach Evidence',
            description: 'Upload the referenced maintenance schedule to the case file for cross-referencing.'
          }
        ]
      });
      setLoading(false);
    }, 1500);
  };

  const toggleFormatting = (format) => {
    setTextFormatting({ ...textFormatting, [format]: !textFormatting[format] });
  };

  const exportPDF = () => {
    alert('Exporting analysis to PDF...');
  };

  const shareAnalysis = () => {
    alert('Sharing analysis...');
  };

  return (
    <div className="argument-analyzer">
      <div className="analyzer-header">
        <div className="header-left">
          <h1>📊 Argument Strength Analyzer</h1>
        </div>
        <div className="header-tabs">
          <button className="tab active">📋 Analysis</button>
          <button className="tab">📜 History</button>
          <button className="tab">⚙️ Settings</button>
        </div>
        <div className="header-actions">
          <button className="action-btn" onClick={exportPDF}>📥 Export PDF</button>
          <button className="action-btn" onClick={shareAnalysis}>📤 Share</button>
        </div>
      </div>

      <div className="analyzer-container">
        {/* Left Panel - Input */}
        <div className="input-panel">
          <section className="input-section">
            <h2>Draft & Input</h2>
            <p>Enter your legal argument or upload a document.</p>

            <div className="argument-input">
              <label>Argument Text</label>
              <div className="text-editor">
                <div className="editor-toolbar">
                  <button 
                    className={`format-btn ${textFormatting.bold ? 'active' : ''}`}
                    onClick={() => toggleFormatting('bold')}
                    title="Bold"
                  >
                    <strong>B</strong>
                  </button>
                  <button 
                    className={`format-btn ${textFormatting.italic ? 'active' : ''}`}
                    onClick={() => toggleFormatting('italic')}
                    title="Italic"
                  >
                    <em>I</em>
                  </button>
                  <button 
                    className={`format-btn ${textFormatting.underline ? 'active' : ''}`}
                    onClick={() => toggleFormatting('underline')}
                    title="Underline"
                  >
                    <u>U</u>
                  </button>
                  <div className="toolbar-divider"></div>
                  <button className="format-btn" title="Bullet List">
                    ≡
                  </button>
                </div>
                <textarea
                  value={argumentText}
                  onChange={(e) => setArgumentText(e.target.value)}
                  placeholder="The Plaintiff asserts that the Defendant's failure to maintain..."
                  className="editor-textarea"
                  rows="12"
                />
              </div>

              <div className="upload-hint">
                <span>📎</span>
                <span>Click to upload .txt, .docx, or .pdf</span>
                <input 
                  type="file" 
                  onChange={handleFileChange}
                  accept=".pdf,.txt,.doc,.docx"
                  className="file-input-hidden"
                />
              </div>
            </div>
          </section>

          <section className="input-section case-context">
            <h3>Case Context</h3>

            <div className="context-field">
              <label>Jurisdiction</label>
              <select value={jurisdiction} onChange={(e) => setJurisdiction(e.target.value)}>
                <option value="">Select Jurisdiction</option>
                <option value="california">California</option>
                <option value="newyork">New York</option>
                <option value="texas">Texas</option>
                <option value="federal">Federal</option>
              </select>
            </div>

            <div className="context-field">
              <label>Case Type</label>
              <select value={caseType} onChange={(e) => setCaseType(e.target.value)}>
                <option value="">Select Case Type</option>
                <option value="tort">Tort / Negligence</option>
                <option value="contract">Contract Dispute</option>
                <option value="criminal">Criminal</option>
                <option value="family">Family Law</option>
              </select>
            </div>

            <div className="context-field">
              <label>Party Role</label>
              <div className="radio-group">
                <label className="radio-option">
                  <input 
                    type="radio" 
                    value="plaintiff"
                    checked={partyRole === 'plaintiff'}
                    onChange={(e) => setPartyRole(e.target.value)}
                  />
                  Plaintiff
                </label>
                <label className="radio-option">
                  <input 
                    type="radio" 
                    value="defendant"
                    checked={partyRole === 'defendant'}
                    onChange={(e) => setPartyRole(e.target.value)}
                  />
                  Defendant
                </label>
              </div>
            </div>

            <div className="context-field">
              <label>Desired Remedy</label>
              <select value={desiredRemedy} onChange={(e) => setDesiredRemedy(e.target.value)}>
                <option value="">Select Remedy</option>
                <option value="damages-monetary">Damages (Monetary)</option>
                <option value="injunction">Injunction</option>
                <option value="specific-performance">Specific Performance</option>
                <option value="restitution">Restitution</option>
              </select>
            </div>

            <button 
              onClick={handleScoreArgument}
              disabled={loading}
              className="btn btn-analyze"
            >
              🔍 {loading ? 'Analyzing...' : 'Analyze Argument Strength'}
            </button>
          </section>
        </div>

        {/* Right Panel - Results */}
        <div className="results-panel">
          {!scoreResult ? (
            <div className="no-results">
              <p>📊 Analysis results will appear here</p>
              <p>Fill in your argument and click "Analyze Argument Strength"</p>
            </div>
          ) : (
            <>
              {/* Overall Score */}
              <div className="score-section">
                <div className="score-circle-large">
                  <span className="score-number">{scoreResult.overallScore}</span>
                  <span className="score-max">/ {scoreResult.maxScore}</span>
                </div>
                <div className="score-text">
                  <h3>{scoreResult.strength}</h3>
                  <p>{scoreResult.summary}</p>
                </div>
              </div>

              {/* Marking Schema Breakdown */}
              <div className="breakdown-section">
                <h3>📊 Marking Schema Breakdown</h3>
                <table className="marking-table">
                  <thead>
                    <tr>
                      <th>Criterion</th>
                      <th>Weight</th>
                      <th>Score</th>
                      <th>Rationale</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scoreResult.markingSchema.map((item, index) => (
                      <tr key={index}>
                        <td className="criterion-name">{item.criterion}</td>
                        <td className="weight">{item.weight}%</td>
                        <td className="score">
                          <span className="score-badge">{item.score}/{item.maxScore}</span>
                        </td>
                        <td className="rationale">{item.rationale}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Weaknesses & Gaps */}
              <div className="weaknesses-section">
                <h3>⚠️ Weaknesses & Gaps</h3>
                <div className="weaknesses-list">
                  {scoreResult.weaknesses.map((weakness, index) => (
                    <div key={index} className="weakness-item">
                      <div className="weakness-icon">⚠️</div>
                      <div className="weakness-content">
                        <h4>{weakness.title}</h4>
                        <p>{weakness.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Improvement Plan */}
              <div className="improvements-section">
                <h3>✅ Improvement Plan</h3>
                <div className="improvements-list">
                  {scoreResult.improvements.map((improvement) => (
                    <div key={improvement.step} className="improvement-item">
                      <div className="improvement-step">{improvement.step}</div>
                      <div className="improvement-content">
                        <h4>{improvement.title}</h4>
                        <p>{improvement.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ArgumentScore;
