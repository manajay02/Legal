import React, { useState, useEffect } from 'react';
import './SimilarCases.css';
import caseService from '../services/caseService';

function SimilarCases() {
  const [caseText, setCaseText] = useState('');
  // eslint-disable-next-line no-unused-vars
  const [uploadedFile, setUploadedFile] = useState(null);
  const [caseType, setCaseType] = useState(null);
  const [detectedType, setDetectedType] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoAnalyzing, setAutoAnalyzing] = useState(false);
  const [step, setStep] = useState('upload'); // upload, processing, results
  const [selectedCase, setSelectedCase] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('text'); // text or file
  const [inputSource, setInputSource] = useState(null); // 'text' or 'pdf' or 'file'
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentLimit, setCurrentLimit] = useState(5);
  const [inputCaseInLibrary, setInputCaseInLibrary] = useState(false); // Track if input case is in library
  const [addingInputCase, setAddingInputCase] = useState(false); // Track adding input case

  // Function to add the INPUT case to library
  const addInputCaseToLibrary = async () => {
    if (inputCaseInLibrary) {
      alert('Your case is already in the library!');
      return;
    }
    
    setAddingInputCase(true);
    try {
      // Generate a title from the first line or first 50 chars
      const firstLine = caseText.split('\n')[0].trim();
      const generatedTitle = firstLine.length > 10 
        ? (firstLine.length > 60 ? firstLine.substring(0, 60) + '...' : firstLine)
        : `My Case - ${new Date().toLocaleDateString()}`;
      
      // Add to database
      const addResponse = await fetch('http://localhost:5000/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: generatedTitle,
          caseType: caseType || detectedType || 'General',
          court: 'User Uploaded',
          year: new Date().getFullYear(),
          outcome: 'Pending',
          content: caseText,
          relevantPoints: []
        })
      });
      
      const result = await addResponse.json();
      
      if (addResponse.ok) {
        setInputCaseInLibrary(true);
        alert('Your case has been added to the library successfully!');
      } else if (result.exists) {
        setInputCaseInLibrary(true);
        alert('This case already exists in the library!');
      } else {
        alert('Failed to add case to library: ' + (result.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error adding input case to library:', err);
      alert('Error adding case to library');
    }
    setAddingInputCase(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    if (inputMode === 'text') {
      const text = e.dataTransfer.getData('text/plain');
      if (text) {
        setCaseText(text);
      }
    } else {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileUpload(files[0]);
      }
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    try {
      setError(null);
      setAutoAnalyzing(true);
      setUploadedFile(file);
      
      // Determine file type
      const fileExtension = file.name.split('.').pop().toLowerCase();
      const fileType = fileExtension === 'pdf' ? 'PDF' : 'Document';
      setInputSource({ type: 'file', name: file.name, fileType: fileType });
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);

      // Upload and convert file to text
      const response = await caseService.uploadAndConvertFile(formData);
      
      if (response.data && response.data.extractedText) {
        setCaseText(response.data.extractedText);
        setDetectedType(response.data.detectedType);
        setCaseType(response.data.detectedType);
        setAutoAnalyzing(false);
      }
    } catch (err) {
      console.error('File upload error:', err);
      setError(err.response?.data?.error || 'Error processing file. Supported formats: PDF, DOCX, TXT, RTF');
      setAutoAnalyzing(false);
    }
  };

  // eslint-disable-next-line no-unused-vars
  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  // Auto-detect case type when text changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (caseText.trim().length > 20 && !detectedType) {
      detectCaseType();
    }
  }, [caseText]);

  const detectCaseType = async () => {
    try {
      setAutoAnalyzing(true);
      const response = await caseService.classifyCase(caseText);
      if (response.data && response.data.predictedType) {
        setDetectedType(response.data.predictedType);
        setCaseType(response.data.predictedType);
      }
      setAutoAnalyzing(false);
    } catch (err) {
      console.log('Auto-detection skipped:', err.message);
      setAutoAnalyzing(false);
    }
  };

  const analyzeSimilarCases = async () => {
    if (!caseText.trim()) {
      setError('Please enter case details or upload a file');
      return;
    }

    if (!caseType) {
      setError('Unable to detect case type. Please try again.');
      return;
    }

    setError(null);
    setLoading(true);
    setStep('processing');
    setUploadProgress(0);
    setCurrentLimit(5);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 30;
      });
    }, 300);

    try {
      // Call actual backend API
      const response = await caseService.findSimilarCases(caseText, caseType, 5);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Transform backend response to match UI expectations
      const similarCases = response.data.results.map((caseItem, index) => ({
        id: caseItem._id || caseItem.caseId,
        caseId: caseItem.caseId,
        title: caseItem.title,
        similarity: caseItem.similarityScore,
        court: caseItem.court || 'Court of Law',
        year: caseItem.year || new Date().getFullYear(),
        category: caseItem.caseType,
        outcome: caseItem.outcome || 'Pending',
        relevantPoints: caseItem.relevantPoints || [],
        fullText: caseItem.fullText || '',
        summary: caseItem.summary || '',
        relevantLaws: caseItem.relevantLaws || [],
        judges: caseItem.judges || [],
        dateOfDecision: caseItem.dateOfDecision
      }));

      setResults({
        found: response.data.found,
        totalFound: response.data.totalFound || response.data.found,
        highestMatch: response.data.highestMatch,
        averageMatch: response.data.averageMatch,
        hasMore: response.data.hasMore || false,
        cases: similarCases
      });

      setLoading(false);
      setStep('results');
    } catch (err) {
      clearInterval(progressInterval);
      console.error('Error finding similar cases:', err);
      setError(err.response?.data?.error || 'Error finding similar cases. Make sure the backend is running on http://localhost:5000');
      setLoading(false);
      setStep('upload');
    }
  };

  // Load more cases function
  const loadMoreCases = async () => {
    setLoadingMore(true);
    const newLimit = currentLimit + 5;
    
    try {
      const response = await caseService.findSimilarCases(caseText, caseType, newLimit);
      
      const similarCases = response.data.results.map((caseItem, index) => ({
        id: caseItem._id || caseItem.caseId,
        caseId: caseItem.caseId,
        title: caseItem.title,
        similarity: caseItem.similarityScore,
        court: caseItem.court || 'Court of Law',
        year: caseItem.year || new Date().getFullYear(),
        category: caseItem.caseType,
        outcome: caseItem.outcome || 'Pending',
        relevantPoints: caseItem.relevantPoints || [],
        fullText: caseItem.fullText || '',
        summary: caseItem.summary || '',
        relevantLaws: caseItem.relevantLaws || [],
        judges: caseItem.judges || [],
        dateOfDecision: caseItem.dateOfDecision
      }));

      setResults({
        found: response.data.found,
        totalFound: response.data.totalFound || response.data.found,
        highestMatch: response.data.highestMatch,
        averageMatch: response.data.averageMatch,
        hasMore: response.data.hasMore || false,
        cases: similarCases
      });
      
      setCurrentLimit(newLimit);
    } catch (err) {
      console.error('Error loading more cases:', err);
    }
    
    setLoadingMore(false);
  };

  const viewCaseDetails = (caseItem) => {
    setSelectedCase(caseItem);
  };

  const closeCaseDetails = () => {
    setSelectedCase(null);
  };

  const resetWorkflow = () => {
    setCaseText('');
    setCaseType(null);
    setDetectedType(null);
    setUploadedFile(null);
    setResults(null);
    setStep('upload');
    setUploadProgress(0);
    setSelectedCase(null);
    setError(null);
    setInputSource(null);
    setCurrentLimit(5);
    setLoadingMore(false);
  };

  return (
    <div className="container">
      <h2>⚖️ Similar Cases Analyzer</h2>

      {/* Workflow Progress */}
      <div className="workflow-progress">
        <div className={`progress-step ${step === 'upload' ? 'active' : step !== 'upload' ? 'completed' : ''}`}>
          <div className="step-number">1</div>
          <p>Upload</p>
        </div>
        <div className="progress-line"></div>
        <div className={`progress-step ${step === 'processing' ? 'active' : step === 'results' ? 'completed' : ''}`}>
          <div className="step-number">2</div>
          <p>Processing</p>
        </div>
        <div className="progress-line"></div>
        <div className={`progress-step ${step === 'results' ? 'active completed' : ''}`}>
          <div className="step-number">3</div>
          <p>Results</p>
        </div>
      </div>

      {/* Upload Step */}
      {step === 'upload' && (
        <div className="card">
          <div className="step-header">
            <h3>📤 Step 1: Upload or Enter Case Details</h3>
            <p>Upload a PDF, Word document, or paste legal case text. The system will automatically detect the case type.</p>
          </div>

          {error && <div className="error-message" style={{ color: '#dc3545', padding: '1rem', background: '#ffe8e8', borderRadius: '8px', marginBottom: '1rem' }}>{error}</div>}

          <div className="upload-section">
            {/* Input Mode Tabs */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '2px solid #eee', paddingBottom: '1rem' }}>
              <button
                onClick={() => setInputMode('text')}
                style={{
                  padding: '0.5rem 1rem',
                  background: inputMode === 'text' ? '#1e3c72' : 'transparent',
                  color: inputMode === 'text' ? 'white' : '#1e3c72',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '0.9rem'
                }}
              >
                ✍️ Text Input
              </button>
              <button
                onClick={() => setInputMode('file')}
                style={{
                  padding: '0.5rem 1rem',
                  background: inputMode === 'file' ? '#1e3c72' : 'transparent',
                  color: inputMode === 'file' ? 'white' : '#1e3c72',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '0.9rem'
                }}
              >
                📁 Upload File
              </button>
            </div>

            {/* Auto-detected Type Display */}
            {detectedType && (
              <div style={{
                background: '#d4edda',
                border: '1px solid #28a745',
                padding: '1rem',
                borderRadius: '8px',
                marginBottom: '1rem',
                color: '#155724',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{ fontSize: '1.2rem' }}>✓</span>
                <div>
                  <strong>Auto-detected Case Type: {detectedType}</strong>
                  <br />
                  <small>{uploadedFile ? `File: ${uploadedFile.name}` : 'Text mode'}</small>
                </div>
              </div>
            )}

            {/* Text Input Mode */}
            {inputMode === 'text' && (
              <div>
                <div className="form-group">
                  <label>Case Text:</label>
                  <textarea
                    value={caseText}
                    onChange={(e) => {
                      setCaseText(e.target.value);
                      if (e.target.value.trim().length > 0) {
                        setInputSource({ type: 'text', name: 'Manual Text Input' });
                      }
                    }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    style={{
                      width: '100%',
                      padding: '1rem',
                      border: '2px dashed #1e3c72',
                      borderRadius: '8px',
                      fontFamily: 'Arial',
                      minHeight: '200px',
                      resize: 'vertical',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Enter or paste case details here... (or drag & drop text)"
                    rows="10"
                  />
                  <small style={{ color: '#666', display: 'block', marginTop: '0.5rem' }}>
                    Minimum 20 characters for auto-detection. Drag & drop text here.
                  </small>
                </div>
              </div>
            )}

            {/* File Upload Mode */}
            {inputMode === 'file' && (
              <div>
                <div className="form-group">
                  <label>Upload Case Document:</label>
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    style={{
                      border: '2px dashed #1e3c72',
                      borderRadius: '8px',
                      padding: '2rem',
                      textAlign: 'center',
                      cursor: 'pointer',
                      background: '#f8f9fa',
                      transition: 'all 0.3s'
                    }}
                  >
                    <p style={{ fontSize: '2rem', margin: '0 0 1rem 0' }}>📄</p>
                    <p style={{ fontSize: '1rem', fontWeight: '600', margin: '0.5rem 0' }}>
                      Drag and drop your file here
                    </p>
                    <p style={{ color: '#666', margin: '0.5rem 0 1rem 0' }}>or</p>
                    <input
                      type="file"
                      accept=".pdf,.docx,.doc,.txt,.rtf,.odt"
                      onChange={handleFileInputChange}
                      style={{ display: 'none' }}
                      id="file-input"
                    />
                    <label
                      htmlFor="file-input"
                      style={{
                        padding: '0.75rem 1.5rem',
                        background: '#1e3c72',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: '600'
                      }}
                    >
                      Browse Files
                    </label>
                    <p style={{ color: '#999', fontSize: '0.85rem', marginTop: '1rem' }}>
                      Supported formats: PDF, DOCX, DOC, TXT, RTF, ODT
                    </p>
                  </div>
                  {uploadedFile && (
                    <div style={{
                      marginTop: '1rem',
                      padding: '0.75rem',
                      background: '#e8f4f8',
                      border: '1px solid #b8d4df',
                      borderRadius: '4px',
                      color: '#004c63'
                    }}>
                      ✓ Selected: <strong>{uploadedFile.name}</strong> ({(uploadedFile.size / 1024).toFixed(2)} KB)
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Auto-detection Indicator */}
            {autoAnalyzing && (
              <div style={{
                textAlign: 'center',
                padding: '1rem',
                color: '#1e3c72',
                fontWeight: '600'
              }}>
                🔄 Auto-detecting case type...
              </div>
            )}
          </div>

          <button
            onClick={analyzeSimilarCases}
            disabled={loading || autoAnalyzing || (!caseText.trim() && !uploadedFile) || !caseType}
            style={{
              width: '100%',
              padding: '1rem',
              background: (loading || autoAnalyzing || !caseText.trim() || !caseType) ? '#ccc' : '#1e3c72',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: (loading || autoAnalyzing || !caseText.trim() || !caseType) ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              marginTop: '1rem'
            }}
          >
            {loading ? 'Processing...' : autoAnalyzing ? 'Detecting...' : '🔍 Find Similar Cases'}
          </button>

          <div style={{ background: '#f0f4f8', padding: '1.5rem', borderRadius: '8px', marginTop: '2rem', borderLeft: '4px solid #1e3c72' }}>
            <h4>💡 How It Works</h4>
            <ul>
              <li>✅ Auto-detects the case type from your input (no manual selection needed)</li>
              <li>✅ Supports PDFs, Word documents, and text files</li>
              <li>✅ Automatically converts files to text</li>
              <li>✅ Extracts legal keywords and concepts</li>
              <li>✅ Searches database for similar cases</li>
              <li>✅ Returns matches ranked by similarity</li>
            </ul>
          </div>
        </div>
      )}

      {/* Processing Step */}
      {step === 'processing' && (
        <div className="card">
          <div className="step-header">
            <h3>⚙️ Step 2: AI Model Processing</h3>
            <p>Analyzing your case with our trained model...</p>
          </div>

          <div className="processing-container">
            <div className="processing-stages">
              <div className="stage processing">
                <div className="stage-icon">📖</div>
                <p>Reading Case</p>
              </div>
              <div className="stage processing">
                <div className="stage-icon">🔍</div>
                <p>Extracting Features</p>
              </div>
              <div className="stage processing">
                <div className="stage-icon">🤖</div>
                <p>Running ML Model</p>
              </div>
              <div className="stage processing">
                <div className="stage-icon">🔗</div>
                <p>Finding Matches</p>
              </div>
            </div>

            <div className="progress-bar-large">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
            </div>
            <p className="progress-text">{Math.round(uploadProgress)}% Complete</p>

            <div className="processing-info">
              <p>📝 Case Type: <strong>{caseType}</strong></p>
              <p>🤖 Model: Legal Case Similarity Analyzer v1.0</p>
              <p>⚡ Backend: Connected to http://localhost:5000</p>
            </div>
          </div>
        </div>
      )}

      {/* Results Step */}
      {step === 'results' && results && (
        <div className="card">
          <div className="step-header">
            <h3>📊 Step 3: Analysis Results</h3>
            <p>Analysis completed - Reviewing your case and similar matches</p>
          </div>

          {/* INPUT CASE SECTION - DISPLAYED FIRST AND PROMINENTLY */}
          <div style={{
            background: '#fff3e0',
            border: '3px solid #ff9800',
            borderRadius: '12px',
            padding: '2rem',
            marginBottom: '3rem',
            boxShadow: '0 4px 6px rgba(255, 152, 0, 0.2)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '1.5rem'
            }}>
              <div style={{
                fontSize: '2.5rem'
              }}>
                {inputSource?.type === 'file' ? '📄' : '✏️'}
              </div>
              <div>
                <h3 style={{ margin: '0 0 0.5rem 0', color: '#e65100' }}>
                  {inputSource?.type === 'file' ? 'UPLOADED DOCUMENT' : 'MANUAL TEXT INPUT'}
                </h3>
                {inputSource?.type === 'file' && (
                  <p style={{ margin: '0', color: '#bf360c', fontWeight: '600' }}>
                    📎 File: {inputSource.name} ({inputSource.fileType})
                  </p>
                )}
                {inputSource?.type === 'text' && (
                  <p style={{ margin: '0', color: '#0277bd', fontWeight: '600' }}>
                    ✍️ User-entered text content
                  </p>
                )}
              </div>
              <div style={{ marginLeft: 'auto' }}>
                <span style={{
                  background: '#1e3c72',
                  color: 'white',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  fontSize: '1rem'
                }}>
                  Case Type: {caseType || detectedType}
                </span>
              </div>
            </div>

            {/* Input Case Text Content */}
            <div style={{
              background: 'white',
              padding: '1.5rem',
              borderRadius: '8px',
              border: '1px solid #ffe0b2',
              marginBottom: '1rem'
            }}>
              <h5 style={{ margin: '0 0 1rem 0', color: '#1e3c72' }}>📋 Case Content</h5>
              <div style={{
                maxHeight: '350px',
                overflowY: 'auto',
                paddingRight: '0.5rem'
              }}>
                <p style={{
                  margin: '0',
                  lineHeight: '1.8',
                  color: '#333',
                  fontSize: '0.95rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'Georgia, serif'
                }}>
                  {caseText.substring(0, 1000)}
                  {caseText.length > 1000 && (
                    <span style={{ color: '#999' }}>
                      <br /><br />... [Content truncated - {caseText.length} total characters] ...
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div style={{
              display: 'flex',
              gap: '2rem',
              padding: '1rem',
              background: '#fffde7',
              borderRadius: '6px',
              fontSize: '0.9rem',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', gap: '2rem' }}>
                <div>
                  <strong>📊 Text Length:</strong> {caseText.length} characters
                </div>
                <div>
                  <strong>📝 Case Type:</strong> {caseType || detectedType}
                </div>
                <div>
                  <strong>⏱️ Analyzed At:</strong> {new Date().toLocaleTimeString()}
                </div>
              </div>
              {/* Uploaded Case Similarity Score - Highlighted */}
              <div style={{
                background: 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)',
                color: 'white',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                boxShadow: '0 4px 15px rgba(255, 107, 53, 0.4)',
                animation: 'pulse 2s infinite'
              }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>🎯 Your Case Match:</span>
                <span style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '800',
                  textShadow: '0 2px 4px rgba(0,0,0,0.2)'
                }}>
                  {results.highestMatch ? `${Math.round(results.highestMatch * 100) / 100}%` : 'N/A'}
                </span>
              </div>
              {/* Add Input Case to Library Button */}
              <button
                onClick={() => addInputCaseToLibrary()}
                disabled={inputCaseInLibrary || addingInputCase}
                style={{
                  padding: '0.75rem 1.25rem',
                  background: inputCaseInLibrary 
                    ? '#9e9e9e' 
                    : 'linear-gradient(135deg, #2e7d32 0%, #43a047 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: inputCaseInLibrary ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  transition: 'all 0.3s',
                  whiteSpace: 'nowrap',
                  boxShadow: inputCaseInLibrary ? 'none' : '0 4px 15px rgba(46,125,50,0.4)',
                  opacity: inputCaseInLibrary ? 0.7 : 1
                }}
                onMouseOver={(e) => {
                  if (!inputCaseInLibrary) {
                    e.currentTarget.style.transform = 'scale(1.02)';
                  }
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                {addingInputCase ? '⏳ Adding...' : 
                 inputCaseInLibrary ? '✓ In Library' : '📚 Add My Case to Library'}
              </button>
            </div>
          </div>

          {/* SIMILAR CASES STATISTICS - All in One Row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <div style={{
              background: 'linear-gradient(135deg, #1e3c72 0%, #2a5a8a 100%)',
              borderRadius: '12px',
              padding: '1.5rem 1rem',
              textAlign: 'center',
              boxShadow: '0 4px 15px rgba(30, 60, 114, 0.3)'
            }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem', color: '#ffffff', fontWeight: '700' }}>
                {results.found}
              </h4>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#a8c0e8', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Showing
              </p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, #2e7d32 0%, #43a047 100%)',
              borderRadius: '12px',
              padding: '1.5rem 1rem',
              textAlign: 'center',
              boxShadow: '0 4px 15px rgba(46, 125, 50, 0.3)'
            }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem', color: '#ffffff', fontWeight: '700' }}>
                {results.totalFound || results.found}
              </h4>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#a5d6a7', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Total Found
              </p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, #f57c00 0%, #ff9800 100%)',
              borderRadius: '12px',
              padding: '1.5rem 1rem',
              textAlign: 'center',
              boxShadow: '0 4px 15px rgba(245, 124, 0, 0.3)'
            }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem', color: '#ffffff', fontWeight: '700' }}>
                {Math.round(results.highestMatch * 100) / 100}%
              </h4>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#ffe0b2', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Highest Match
              </p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, #7b1fa2 0%, #9c27b0 100%)',
              borderRadius: '12px',
              padding: '1.5rem 1rem',
              textAlign: 'center',
              boxShadow: '0 4px 15px rgba(123, 31, 162, 0.3)'
            }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem', color: '#ffffff', fontWeight: '700' }}>
                {Math.round(results.averageMatch * 100) / 100}%
              </h4>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#e1bee7', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Average Match
              </p>
            </div>
          </div>

          {/* SIMILAR CASES SECTION - DISPLAYED BELOW */}
          <div className="results-section" style={{ marginTop: '2rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1.5rem',
              paddingBottom: '1rem',
              borderBottom: '2px solid #1e3c72'
            }}>
              <h4 style={{ 
                margin: 0, 
                color: '#1e3c72', 
                fontSize: '1.3rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                ⚖️ Similar Cases Ranked by Similarity Score
              </h4>
              <span style={{
                background: '#1e3c72',
                color: 'white',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                fontSize: '0.9rem'
              }}>
                Showing {results.cases.length} of {results.totalFound || results.cases.length}
              </span>
            </div>
            
            {results.cases && results.cases.length > 0 ? (
              <>
                {/* Table Body - No Header */}
                <div className="results-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {results.cases.map((result, index) => (
                    <div key={index} className="result-card" style={{
                      display: 'grid',
                      gridTemplateColumns: '70px 1fr 1fr 130px',
                      background: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '10px',
                      alignItems: 'stretch',
                      transition: 'all 0.2s',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                      overflow: 'hidden'
                    }}>
                      {/* Rank Column */}
                      <div style={{
                        padding: '1rem 0.5rem',
                        textAlign: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'linear-gradient(135deg, #1e3c72 0%, #2a5a8a 100%)',
                        color: 'white'
                      }}>
                        <span style={{ fontSize: '0.65rem', opacity: 0.8, marginBottom: '0.2rem' }}>RANK</span>
                        <span style={{ fontSize: '1.8rem', fontWeight: 'bold' }}>#{index + 1}</span>
                      </div>
                      
                      {/* Case Details Column - Now includes Status */}
                      <div style={{ 
                        padding: '1rem 1.25rem', 
                        borderRight: '1px solid #e2e8f0',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center'
                      }}>
                        <h5 style={{ 
                          margin: '0 0 0.6rem 0', 
                          color: '#1a365d', 
                          fontSize: '1rem',
                          fontWeight: '700',
                          lineHeight: '1.3'
                        }}>
                          {result.title.length > 50 ? result.title.substring(0, 50) + '...' : result.title}
                        </h5>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                          <span style={{
                            background: '#e3f2fd',
                            color: '#0d47a1',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.7rem',
                            fontWeight: '600'
                          }}>
                            ⚖️ {result.court}
                          </span>
                          <span style={{
                            background: '#fff3e0',
                            color: '#e65100',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.7rem',
                            fontWeight: '600'
                          }}>
                            📅 {result.year}
                          </span>
                          <span style={{
                            background: '#fce4ec',
                            color: '#880e4f',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.7rem',
                            fontWeight: '600'
                          }}>
                            📁 {result.category}
                          </span>
                          <span style={{
                            background: result.outcome === 'Won' ? '#e8f5e9' : result.outcome === 'Lost' ? '#ffebee' : '#f5f5f5',
                            color: result.outcome === 'Won' ? '#1b5e20' : result.outcome === 'Lost' ? '#b71c1c' : '#424242',
                            padding: '0.25rem 0.6rem',
                            borderRadius: '4px',
                            fontSize: '0.7rem',
                            fontWeight: '700',
                            border: result.outcome === 'Won' ? '1px solid #4caf50' : result.outcome === 'Lost' ? '1px solid #ef5350' : '1px solid #9e9e9e'
                          }}>
                            {result.outcome === 'Won' ? '✓ Won' : result.outcome === 'Lost' ? '✗ Lost' : '● ' + result.outcome}
                          </span>
                        </div>
                        {/* Similarity Score at bottom */}
                        <div style={{
                          marginTop: '0.75rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem'
                        }}>
                          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: '500' }}>Similarity:</span>
                          <span style={{ 
                            fontSize: '1.1rem', 
                            fontWeight: 'bold',
                            color: result.similarity > 70 ? '#2e7d32' : result.similarity > 50 ? '#e65100' : '#1565c0'
                          }}>
                            {Math.round(result.similarity * 100) / 100}%
                          </span>
                          <div style={{
                            flex: 1,
                            maxWidth: '150px',
                            height: '6px',
                            background: '#e0e0e0',
                            borderRadius: '3px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              height: '100%',
                              width: `${Math.min(result.similarity, 100)}%`,
                              background: result.similarity > 70 ? '#4caf50' : result.similarity > 50 ? '#ff9800' : '#2196f3',
                              borderRadius: '3px'
                            }}></div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Key Points Column */}
                      <div style={{
                        padding: '1rem 1.25rem',
                        borderRight: '1px solid #e2e8f0',
                        display: 'flex',
                        alignItems: 'center',
                        fontSize: '0.85rem',
                        color: '#4a5568',
                        lineHeight: '1.5'
                      }}>
                        {result.relevantPoints && result.relevantPoints.length > 0 ? (
                          <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                            {result.relevantPoints.slice(0, 2).map((point, i) => (
                              <li key={i} style={{ marginBottom: '0.3rem' }}>
                                {point.length > 70 ? point.substring(0, 70) + '...' : point}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span style={{ color: '#a0aec0', fontStyle: 'italic' }}>No key points available</span>
                        )}
                      </div>
                      
                      {/* Action Column */}
                      <div style={{
                        padding: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100%'
                      }}>
                        <button
                          onClick={() => viewCaseDetails(result)}
                          style={{
                            padding: '0.75rem 1.5rem',
                            background: 'linear-gradient(135deg, #1e3c72 0%, #2a5a8a 100%)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: '600',
                            fontSize: '0.85rem',
                            transition: 'all 0.3s',
                            whiteSpace: 'nowrap',
                            boxShadow: '0 2px 8px rgba(30,60,114,0.2)'
                          }}
                          onMouseOver={(e) => {
                            e.currentTarget.style.transform = 'scale(1.05)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(30,60,114,0.4)';
                          }}
                          onMouseOut={(e) => {
                            e.currentTarget.style.transform = 'scale(1)';
                            e.currentTarget.style.boxShadow = '0 2px 8px rgba(30,60,114,0.2)';
                          }}
                        >
                          📄 View Details
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>No similar cases found in database. Try adding more cases first.</p>
            )}

            {/* Load More Button */}
            {results.hasMore && (
              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button
                  onClick={loadMoreCases}
                  disabled={loadingMore}
                  style={{
                    padding: '1rem 3rem',
                    background: loadingMore ? '#ccc' : 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: loadingMore ? 'not-allowed' : 'pointer',
                    fontWeight: '700',
                    fontSize: '1rem',
                    boxShadow: '0 4px 12px rgba(255, 152, 0, 0.3)',
                    transition: 'all 0.3s'
                  }}
                >
                  {loadingMore ? '⏳ Loading...' : `📚 Load More Cases (${results.totalFound - results.found} more available)`}
                </button>
              </div>
            )}
          </div>

          <button className="btn btn-primary btn-block" onClick={resetWorkflow} style={{ marginTop: '2rem' }}>
            ← Analyze Another Case
          </button>
        </div>
      )}

      {/* Case Details Modal - Full Case Document View */}
      {selectedCase && (
        <div 
          className="modal-overlay" 
          onClick={closeCaseDetails}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem'
          }}
        >
          <div 
            className="modal-content" 
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '12px',
              width: '90%',
              maxWidth: '900px',
              maxHeight: '90vh',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {/* Modal Header */}
            <div style={{
              background: 'linear-gradient(135deg, #1e3c72 0%, #2a5a8a 100%)',
              color: 'white',
              padding: '1.5rem 2rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'start'
            }}>
              <div>
                <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.3rem' }}>
                  📄 Case Document: {selectedCase.caseId || selectedCase.id}
                </h3>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ background: 'rgba(255,255,255,0.2)', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.85rem' }}>
                    ⚖️ {selectedCase.court}
                  </span>
                  <span style={{ background: 'rgba(255,255,255,0.2)', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.85rem' }}>
                    📅 {selectedCase.year}
                  </span>
                  <span style={{ background: 'rgba(255,255,255,0.2)', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.85rem' }}>
                    📁 {selectedCase.category}
                  </span>
                  <span style={{ 
                    background: selectedCase.outcome === 'Won' ? '#4caf50' : selectedCase.outcome === 'Lost' ? '#f44336' : '#ff9800',
                    padding: '0.25rem 0.75rem', 
                    borderRadius: '4px', 
                    fontSize: '0.85rem',
                    fontWeight: '600'
                  }}>
                    {selectedCase.outcome}
                  </span>
                </div>
              </div>
              <button 
                onClick={closeCaseDetails}
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  border: 'none',
                  color: 'white',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ×
              </button>
            </div>

            {/* Similarity Score Bar */}
            <div style={{
              background: '#f5f5f5',
              padding: '1rem 2rem',
              borderBottom: '1px solid #ddd'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ fontWeight: '600', color: '#1e3c72' }}>Similarity Score:</span>
                <div style={{
                  flex: 1,
                  background: '#e0e0e0',
                  height: '12px',
                  borderRadius: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: selectedCase.similarity > 70 ? '#4caf50' : selectedCase.similarity > 50 ? '#ff9800' : '#2196f3',
                    height: '100%',
                    width: `${Math.min(selectedCase.similarity, 100)}%`
                  }}></div>
                </div>
                <span style={{
                  background: '#1e3c72',
                  color: 'white',
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  fontWeight: 'bold',
                  fontSize: '1.1rem'
                }}>
                  {Math.round(selectedCase.similarity * 100) / 100}%
                </span>
              </div>
            </div>

            {/* Modal Body - Scrollable */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '2rem'
            }}>
              {/* Case Title */}
              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#1e3c72' }}>📌 Case Title</h4>
                <p style={{ 
                  margin: 0, 
                  fontSize: '1.1rem', 
                  color: '#333',
                  background: '#f9f9f9',
                  padding: '1rem',
                  borderRadius: '6px',
                  borderLeft: '4px solid #1e3c72'
                }}>
                  {selectedCase.title}
                </p>
              </div>

              {/* Summary */}
              {selectedCase.summary && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: '#1e3c72' }}>📝 Summary</h4>
                  <p style={{ 
                    margin: 0, 
                    lineHeight: '1.7', 
                    color: '#444',
                    background: '#fff3e0',
                    padding: '1rem',
                    borderRadius: '6px',
                    borderLeft: '4px solid #ff9800'
                  }}>
                    {selectedCase.summary}
                  </p>
                </div>
              )}

              {/* Full Case Text - THE MAIN CONTENT */}
              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ 
                  margin: '0 0 0.5rem 0', 
                  color: '#1e3c72',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  📄 Full Case Document
                  <span style={{
                    background: '#e3f2fd',
                    color: '#1565c0',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '4px',
                    fontSize: '0.8rem',
                    fontWeight: 'normal'
                  }}>
                    {selectedCase.fullText?.length || 0} characters
                  </span>
                </h4>
                <div style={{ 
                  background: '#fafafa',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  maxHeight: '400px',
                  overflowY: 'auto'
                }}>
                  <pre style={{ 
                    margin: 0, 
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontFamily: 'Georgia, serif',
                    fontSize: '0.95rem',
                    lineHeight: '1.8',
                    color: '#333'
                  }}>
                    {selectedCase.fullText || 'Full case text not available.'}
                  </pre>
                </div>
              </div>

              {/* Relevant Laws */}
              {selectedCase.relevantLaws && selectedCase.relevantLaws.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: '#1e3c72' }}>⚖️ Relevant Laws</h4>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {selectedCase.relevantLaws.map((law, i) => (
                      <span key={i} style={{
                        background: '#e8f5e9',
                        color: '#2e7d32',
                        padding: '0.5rem 1rem',
                        borderRadius: '4px',
                        fontSize: '0.9rem'
                      }}>
                        {law}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Points */}
              {selectedCase.relevantPoints && selectedCase.relevantPoints.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: '#1e3c72' }}>🔑 Key Points</h4>
                  <ul style={{
                    margin: 0,
                    paddingLeft: '1.5rem',
                    background: '#f3e5f5',
                    padding: '1rem 1rem 1rem 2rem',
                    borderRadius: '6px',
                    borderLeft: '4px solid #9c27b0'
                  }}>
                    {selectedCase.relevantPoints.map((point, i) => (
                      <li key={i} style={{ marginBottom: '0.5rem', color: '#444' }}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '1rem 2rem',
              background: '#f5f5f5',
              borderTop: '1px solid #ddd',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '1rem'
            }}>
              <button
                onClick={closeCaseDetails}
                style={{
                  padding: '0.75rem 2rem',
                  background: '#1e3c72',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SimilarCases;
