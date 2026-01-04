import React, { useState } from 'react';
import caseService from '../services/caseService';
import './Upload.css';

function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await caseService.uploadPDF(formData);
      setExtractedText(response.data.text);
    } catch (err) {
      setError('Error uploading file: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container upload-page">
      <h2>Upload Legal Document</h2>
      
      <div className="upload-card">
        <div className="upload-section">
          <h3>📤 Select PDF File</h3>
          <input 
            type="file" 
            accept=".pdf"
            onChange={handleFileChange}
            className="file-input"
          />
          <button 
            onClick={handleUpload}
            disabled={loading}
            className="btn btn-primary btn-upload"
          >
            {loading ? 'Processing...' : 'Upload & Extract'}
          </button>
          {error && <div className="error-message">{error}</div>}
        </div>

        {extractedText && (
          <div className="extracted-section">
            <h3>📄 Extracted Text</h3>
            <textarea 
              value={extractedText}
              readOnly
              className="extracted-textarea"
            />
            <button className="btn btn-secondary">Copy Text</button>
            <button className="btn btn-primary">Classify This Case</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;
