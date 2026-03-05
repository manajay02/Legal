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
  const [documentType, setDocumentType] = useState('employment');
  const fileInputRef = useRef(null);

  const documentTypes = [
    { value: 'employment', label: 'Employment Contract', icon: '👔' },
    { value: 'rental', label: 'Rental Agreement', icon: '🏠' },
    { value: 'sales', label: 'Sales Contract', icon: '📦' },
    { value: 'service', label: 'Service Agreement', icon: '🛠️' },
    { value: 'nda', label: 'Non-Disclosure Agreement', icon: '🔒' },
    { value: 'other', label: 'Other Legal Document', icon: '📄' },
  ];

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
    formData.append('document_type', documentType);

    try {
      const response = await axios.post('http://localhost:8002/upload-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      // Use backend's detected domain/document_type - don't override
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
      // Use backend's detected domain/document_type - don't override
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
            <span className="hero-icon">📋</span>
            Legal Document Compliance Analyzer
          </h1>
          <p className="hero-subtitle">
            Upload your legal documents and get instant AI-powered compliance analysis 
            against Sri Lankan laws and regulations
          </p>
        </div>
      </div>

      {/* Main Upload Container */}
      <div className="upload-container">
        {/* Document Type Selector */}
        <div className="document-type-section">
          <h3 className="section-title">
            <span className="section-icon">📑</span>
            Select Document Type
          </h3>
          <div className="document-type-grid">
            {documentTypes.map((type) => (
              <button
                key={type.value}
                className={`document-type-btn ${documentType === type.value ? 'active' : ''}`}
                onClick={() => setDocumentType(type.value)}
              >
                <span className="doc-type-icon">{type.icon}</span>
                <span className="doc-type-label">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Upload Mode Toggle */}
        <div className="mode-toggle-section">
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
            <span>{error}</span>
          </div>
        )}

        {/* Security Notice */}
        <div className="security-notice">
          <div className="security-icon">🔐</div>
          <div className="security-text">
            <strong>Your privacy is protected</strong>
            <p>Documents are processed in real-time and are never stored on our servers. 
            All analysis is performed securely using encrypted connections.</p>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section">
        <div className="feature-card">
          <div className="feature-icon">⚡</div>
          <h4>Instant Analysis</h4>
          <p>Get compliance results in seconds with our AI-powered engine</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📚</div>
          <h4>Sri Lankan Laws</h4>
          <p>Analysis based on Shop and Office Employees Act & more</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">✅</div>
          <h4>Mandatory Checks</h4>
          <p>Identify missing required clauses for your document type</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h4>Detailed Reports</h4>
          <p>Comprehensive breakdown with confidence scores</p>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
