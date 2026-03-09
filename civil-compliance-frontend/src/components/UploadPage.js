import React, { useState, useRef } from 'react';
import axios from 'axios';
import '../styles/UploadPage.css';

function UploadPage({ onResults }) {
  const [file, setFile] = useState(null);
  const [contractText, setContractText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadMode, setUploadMode] = useState('file');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const supportedFormats = [
    { ext: 'PDF', icon: '📕', color: '#dc2626' },
    { ext: 'TXT', icon: '📝', color: '#2563eb' },
    { ext: 'DOCX', icon: '📘', color: '#1d4ed8' },
  ];

  const handleFileSelect = (selectedFile) => {
    const validTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const validExtensions = ['.pdf', '.txt', '.docx'];
    
    const fileExtension = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'));
    
    if (validTypes.includes(selectedFile.type) || validExtensions.includes(fileExtension)) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid file (PDF, TXT, or DOCX)');
      setFile(null);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDropZoneClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8002/upload-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      onResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze document');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!contractText.trim()) {
      setError('Please enter contract text');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8002/check', {
        contract_text: contractText,
      });
      onResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to check compliance');
    } finally {
      setLoading(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (fileName) => {
    const ext = fileName.toLowerCase().split('.').pop();
    switch (ext) {
      case 'pdf': return '📕';
      case 'txt': return '📝';
      case 'docx': return '📘';
      default: return '📄';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="upload-page">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
         
          <h1 className="hero-title">
            <span className="hero-icon">⚖️</span>
            Legal Document Compliance Analyzer
          </h1>
          <p className="hero-subtitle">
            Upload your legal documents and get instant AI-powered compliance analysis 
            against Sri Lankan laws and regulations. Our system automatically detects 
            document types and analyzes them accordingly.
          </p>
        </div>
      </div>

      {/* Main Upload Container */}
      <div className="upload-container">
        {/* Upload Mode Toggle */}
        <div className="mode-toggle-section">
          <h3 className="section-title">
            <span className="section-icon">📤</span>
            Upload Your Document
          </h3>
          <div className="mode-toggle">
            <button 
              className={`mode-btn ${uploadMode === 'file' ? 'active' : ''}`}
              onClick={() => setUploadMode('file')}
            >
              <span className="mode-icon">📁</span>
              Upload File
            </button>
            <button 
              className={`mode-btn ${uploadMode === 'text' ? 'active' : ''}`}
              onClick={() => setUploadMode('text')}
            >
              <span className="mode-icon">✍️</span>
              Paste Text
            </button>
          </div>
        </div>

        {/* File Upload Section */}
        {uploadMode === 'file' && (
          <div className="file-upload-section">
            <div 
              className={`drop-zone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleDropZoneClick}
            >
              <input
                type="file"
                ref={fileInputRef}
                accept=".pdf,.txt,.docx"
                onChange={handleFileChange}
                className="file-input-hidden"
              />
              
              {!file ? (
                <div className="drop-zone-content">
                  <div className="upload-icon-container">
                    <span className="upload-icon">☁️</span>
                    <span className="upload-arrow">⬆️</span>
                  </div>
                  <h4 className="drop-zone-title">
                    {isDragging ? 'Drop your file here' : 'Drag & Drop your document'}
                  </h4>
                  <p className="drop-zone-subtitle">or click to browse files</p>
                </div>
              ) : (
                <div className="file-preview" onClick={(e) => e.stopPropagation()}>
                  <div className="file-icon">{getFileIcon(file.name)}</div>
                  <div className="file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{formatFileSize(file.size)}</span>
                  </div>
                  <button className="remove-file-btn" onClick={removeFile}>✕</button>
                </div>
              )}
            </div>

            {/* Supported Formats */}
            <div className="supported-formats">
              <span className="formats-label">Supported formats:</span>
              <div className="format-badges">
                {supportedFormats.map((format) => (
                  <span 
                    key={format.ext} 
                    className="format-badge"
                    style={{ '--badge-color': format.color }}
                  >
                    {format.icon} {format.ext}
                  </span>
                ))}
              </div>
            </div>

            {/* Analyze Button */}
            <button 
              className={`analyze-btn ${loading ? 'loading' : ''}`}
              onClick={handleFileUpload}
              disabled={loading || !file}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  <span>Analyzing Document...</span>
                </>
              ) : (
                <>
                  <span className="btn-icon">🔍</span>
                  <span>Analyze Document</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Text Input Section */}
        {uploadMode === 'text' && (
          <div className="text-input-section">
            <div className="textarea-container">
              <textarea
                value={contractText}
                onChange={(e) => setContractText(e.target.value)}
                placeholder="Paste your contract or legal document text here...

Example:
The Employee shall report to the General Manager and shall perform duties reasonably related to the Employee's position. 
The Employee will receive a monthly salary of Rs 50,000..."
                rows={12}
              />
              <div className="char-count">
                {contractText.length} characters
              </div>
            </div>

            <button 
              className={`analyze-btn ${loading ? 'loading' : ''}`}
              onClick={handleTextSubmit}
              disabled={loading || !contractText.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  <span>Checking Compliance...</span>
                </>
              ) : (
                <>
                  <span className="btn-icon">🔍</span>
                  <span>Check Compliance</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <div className="error-content">
              <strong className="error-title">Document Rejected</strong>
              <span className="error-detail">{error}</span>
            </div>
          </div>
        )}

        {/* Security Notice */}
        <div className="security-notice">
          <div className="security-icon">🔐</div>
          <div className="security-text">
            <strong>Your privacy is protected</strong>
            <p>Documents are processed securely. Analysis results are stored for your reference 
            and can be accessed from your history at any time.</p>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-container">
        <div className="features-box">
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h4>Instant Analysis</h4>
              <p>Get compliance results in seconds with our AI-powered Legal-BERT engine</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📚</div>
              <h4>Sri Lankan Laws</h4>
              <p>Analysis based on Shop and Office Employees Act, EPF/ETF & more</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">✅</div>
              <h4>Mandatory Checks</h4>
              <p>Identify missing required clauses for your document type</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h4>Detailed Reports</h4>
              <p>Comprehensive breakdown with confidence scores & export options</p>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="how-it-works-section">
        <h3 className="section-heading">How It Works</h3>
        <div className="steps-container">
          <div className="step-card">
            <div className="step-number">1</div>
            <div className="step-icon">📤</div>
            <h4>Upload Document</h4>
            <p>Upload your legal document in PDF, DOCX, or TXT format</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">2</div>
            <div className="step-icon">🤖</div>
            <h4>AI Analysis</h4>
            <p>Our Legal-BERT model analyzes your document against Sri Lankan laws</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">3</div>
            <div className="step-icon">📋</div>
            <h4>Get Results</h4>
            <p>Receive detailed compliance report with recommendations</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">4</div>
            <div className="step-icon">🔍</div>
            <h4>Check Missing Clauses</h4>
            <p>View mandatory clauses status and identify missing requirements</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step-card">
            <div className="step-number">5</div>
            <div className="step-icon">⬇️</div>
            <h4>Download Report</h4>
            <p>Export comprehensive PDF report for your records</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
