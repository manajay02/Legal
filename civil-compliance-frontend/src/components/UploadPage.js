import React, { useState } from 'react';
import axios from 'axios';
import '../styles/UploadPage.css';

function UploadPage({ onResults }) {
  const [file, setFile] = useState(null);
  const [contractText, setContractText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadMode, setUploadMode] = useState('pdf'); // 'pdf' or 'text'

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
      setFile(null);
    }
  };

  const handlePdfUpload = async () => {
    if (!file) {
      setError('Please select a PDF file');
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
      setError(err.response?.data?.detail || 'Failed to analyze PDF');
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

  return (
    <div className="upload-page">
      <div className="upload-container">
        <h2>Upload Contract for Compliance Check</h2>
        
        <div className="mode-toggle">
          <button 
            className={uploadMode === 'pdf' ? 'active' : ''} 
            onClick={() => setUploadMode('pdf')}
          >
            📄 Upload PDF
          </button>
          <button 
            className={uploadMode === 'text' ? 'active' : ''} 
            onClick={() => setUploadMode('text')}
          >
            ✍️ Enter Text
          </button>
        </div>

        {uploadMode === 'pdf' ? (
          <div className="pdf-upload-section">
            <div className="file-input-wrapper">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                id="pdf-input"
              />
              <label htmlFor="pdf-input" className="file-label">
                {file ? file.name : 'Choose PDF file...'}
              </label>
            </div>
            <button 
              onClick={handlePdfUpload} 
              disabled={loading || !file}
              className="submit-btn"
            >
              {loading ? 'Analyzing...' : 'Analyze PDF'}
            </button>
          </div>
        ) : (
          <div className="text-input-section">
            <textarea
              value={contractText}
              onChange={(e) => setContractText(e.target.value)}
              placeholder="Paste your contract text here..."
              rows={10}
            />
            <button 
              onClick={handleTextSubmit} 
              disabled={loading || !contractText.trim()}
              className="submit-btn"
            >
              {loading ? 'Checking...' : 'Check Compliance'}
            </button>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  );
}

export default UploadPage;
