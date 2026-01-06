import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.type === 'application/pdf' || selectedFile.type === 'text/plain') {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a PDF or TXT file');
        setFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/api/cases/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Always proceed to results
      localStorage.setItem('uploadedCase', JSON.stringify(response.data));
      navigate('/results', { state: { caseData: response.data } });
    } catch (err) {
      setError('Error uploading file. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileChange({ target: { files: [droppedFile] } });
    }
  };

  return (
    <div className="App">
      <div className="hero-section">
        <h1>⚖️ Legal Case Analyzer</h1>
        <p className="lead">Upload a legal document to find similar cases and get intelligent insights</p>
      </div>

      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-8">
            {error && <div className="error-alert">{error}</div>}

            <div
              className="upload-card"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => document.getElementById('fileInput').click()}
            >
              <div style={{ fontSize: '48px', marginBottom: '15px' }}>📄</div>
              <h4>Drag & Drop Your Document</h4>
              <p className="text-muted">or click to browse</p>
              <p style={{ fontSize: '0.9rem', color: '#666' }}>
                Supported formats: PDF, TXT (Max 10MB)
              </p>
              <input
                id="fileInput"
                type="file"
                hidden
                accept=".pdf,.txt"
                onChange={handleFileChange}
              />
            </div>

            {file && (
              <div style={{ marginTop: '20px', textAlign: 'center' }}>
                <p className="text-success">✓ File selected: <strong>{file.name}</strong></p>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleUpload}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span
                        className="spinner-border spinner-border-sm me-2"
                        role="status"
                        aria-hidden="true"
                      ></span>
                      Analyzing...
                    </>
                  ) : (
                    'Analyze Document'
                  )}
                </button>
              </div>
            )}

            <div style={{ marginTop: '40px', padding: '20px', backgroundColor: '#e7f3ff', borderRadius: '8px' }}>
              <h5>📋 How it works:</h5>
              <ol>
                <li>Upload a legal document (PDF or TXT)</li>
                <li>Our AI validates if it's a legal case</li>
                <li>If valid, we find similar cases from our database</li>
                <li>View results with similarity scores</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
