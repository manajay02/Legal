import React, { useState, useRef } from 'react';
import axios from 'axios';
import '../styles/UploadPage.css';

function UploadPage({ onResults }) {
  const [file, setFile] = useState(null);
  const [contractText, setContractText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadMode, setUploadMode] = useState('file'); // 'file' or 'text'
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const supportedFormats = [
    { ext: 'PDF', icon: '📄', color: '#e74c3c' },
    { ext: 'TXT', icon: '📝', color: '#3498db' },
    { ext: 'DOCX', icon: '📃', color: '#2980b9' }
  ];

  const handleFileChange = (selectedFile) => {
    if (!selectedFile) return;
    
    const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const allowedExtensions = ['.pdf', '.txt', '.docx'];
    const fileExtension = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'));
    
    if (allowedTypes.includes(selectedFile.type) || allowedExtensions.includes(fileExtension)) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid file (PDF, TXT, or DOCX)');
      setFile(null);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    const droppedFile = e.dataTransfer.files[0];
    handleFileChange(droppedFile);
  };

  const handleFileInputChange = (e) => {
    handleFileChange(e.target.files[0]);
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
      onResults(response.data, file.name);
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
      onResults(response.data, 'text-input');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to check compliance');
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = () => {
    if (!file) return null;
    const ext = file.name.split('.').pop().toUpperCase();
    const format = supportedFormats.find(f => f.ext === ext);
    return format ? format.icon : '📎';
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="upload-page">
      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="loading-spinner">
              <div className="spinner-ring"></div>
              <div className="spinner-ring"></div>
              <div className="spinner-ring"></div>
            </div>
            <h3>Analyzing Document</h3>
            <p>Please wait while our AI processes your document...</p>
            <div className="loading-steps">
              <div className="step active">
                <span className="step-icon">📄</span>
                <span>Extracting Text</span>
              </div>
              <div className="step">
                <span className="step-icon">🔍</span>
                <span>Identifying Clauses</span>
              </div>
              <div className="step">
                <span className="step-icon">⚖️</span>
                <span>Checking Compliance</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="upload-container">
        {/* Header Section */}
        <div className="upload-header">
          <div className="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10,9 9,9 8,9"/>
            </svg>
          </div>
          <h2>Upload Contract for Compliance Check</h2>
          <p className="header-subtitle">
            Upload your legal document and let our AI analyze it against Sri Lankan civil law
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="mode-toggle">
          <button 
            className={`mode-btn ${uploadMode === 'file' ? 'active' : ''}`}
            onClick={() => setUploadMode('file')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span>Upload File</span>
          </button>
          <button 
            className={`mode-btn ${uploadMode === 'text' ? 'active' : ''}`}
            onClick={() => setUploadMode('text')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            <span>Paste Text</span>
          </button>
        </div>

        {/* File Upload Section */}
        {uploadMode === 'file' && (
          <div className="file-upload-section">
            {/* Drag & Drop Zone */}
            <div 
              className={`dropzone ${isDragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={!file ? handleBrowseClick : undefined}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={handleFileInputChange}
                className="file-input-hidden"
              />
              
              {!file ? (
                <div className="dropzone-content">
                  <div className="dropzone-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
                      <path d="M12 12v9"/>
                      <path d="M8 17l4-5 4 5"/>
                    </svg>
                  </div>
                  <h3>Drag & Drop your file here</h3>
                  <p>or click to browse from your computer</p>
                </div>
              ) : (
                <div className="file-preview">
                  <div className="file-icon">{getFileIcon()}</div>
                  <div className="file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{formatFileSize(file.size)}</span>
                  </div>
                  <button className="remove-file-btn" onClick={(e) => { e.stopPropagation(); handleRemoveFile(); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
              )}
            </div>

            {/* Supported Formats */}
            <div className="supported-formats">
              <span className="formats-label">Supported formats:</span>
              <div className="format-badges">
                {supportedFormats.map((format) => (
                  <span key={format.ext} className="format-badge" style={{ '--format-color': format.color }}>
                    {format.icon} {format.ext}
                  </span>
                ))}
              </div>
            </div>

            {/* Analyze Button */}
            <button 
              className={`analyze-btn ${file ? 'ready' : ''}`}
              onClick={handleFileUpload}
              disabled={loading || !file}
            >
              <span className="btn-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </span>
              <span className="btn-text">Analyze Document</span>
              <span className="btn-arrow">→</span>
            </button>
          </div>
        )}

        {/* Text Input Section */}
        {uploadMode === 'text' && (
          <div className="text-input-section">
            <div className="textarea-wrapper">
              <textarea
                value={contractText}
                onChange={(e) => setContractText(e.target.value)}
                placeholder="Paste your contract text here...

Example:
This employment agreement is made between ABC Company and John Doe. 
The employee shall receive a monthly salary of Rs. 50,000...
The working hours shall be from 9:00 AM to 5:00 PM..."
                rows={12}
              />
              <div className="textarea-footer">
                <span className="char-count">{contractText.length} characters</span>
              </div>
            </div>

            <button 
              className={`analyze-btn ${contractText.trim() ? 'ready' : ''}`}
              onClick={handleTextSubmit}
              disabled={loading || !contractText.trim()}
            >
              <span className="btn-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </span>
              <span className="btn-text">Check Compliance</span>
              <span className="btn-arrow">→</span>
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Features Section */}
        <div className="features-section">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h4>Smart Analysis</h4>
            <p>AI-powered clause detection and classification</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚖️</div>
            <h4>Legal Compliance</h4>
            <p>Checks against Sri Lankan civil law statutes</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h4>Detailed Reports</h4>
            <p>Comprehensive compliance reports with explanations</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
