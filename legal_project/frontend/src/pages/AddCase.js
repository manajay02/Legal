import React, { useState } from 'react';
import './AddCase.css';
import caseService from '../services/caseService';

function AddCase() {
  const [formData, setFormData] = useState({
    title: '',
    summary: '',
    caseType: 'Civil',
    court: '',
    year: new Date().getFullYear(),
    keyPoints: '',
    outcome: 'Pending'
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.title.trim()) {
      setError('Case title is required');
      return;
    }
    if (!formData.summary.trim()) {
      setError('Case summary is required');
      return;
    }

    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      // Parse keyPoints from comma-separated values
      const keyPoints = formData.keyPoints
        .split(',')
        .map(point => point.trim())
        .filter(point => point.length > 0);

      const caseData = {
        title: formData.title,
        summary: formData.summary,
        caseType: formData.caseType,
        court: formData.court || undefined,
        year: parseInt(formData.year),
        keyPoints,
        outcome: formData.outcome
      };

      const response = await caseService.addCase(caseData);

      if (response.data.success) {
        setMessage(`✓ Case "${formData.title}" added successfully!`);
        
        // Reset form
        setFormData({
          title: '',
          summary: '',
          caseType: 'Civil',
          court: '',
          year: new Date().getFullYear(),
          keyPoints: '',
          outcome: 'Pending'
        });

        // Clear message after 3 seconds
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (err) {
      console.error('Error adding case:', err);
      setError(err.response?.data?.error || 'Error adding case. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const caseTypes = [
    'Civil', 'Criminal', 'Labour', 'Family', 'Financial',
    'Drug', 'Environmental', 'Tax', 'Terrorism', 'Sexual Cases',
    'Sports', 'Asset', 'Contempt of Court'
  ];

  return (
    <div className="container">
      <h2>📋 Add Case to Database</h2>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Add a new case to the database. This case will be used for similarity matching and analysis.
      </p>

      {message && (
        <div style={{
          background: '#d4edda',
          border: '1px solid #28a745',
          color: '#155724',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem'
        }}>
          {message}
        </div>
      )}

      {error && (
        <div style={{
          background: '#ffe8e8',
          border: '1px solid #dc3545',
          color: '#dc3545',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem'
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card">
        {/* Case Title */}
        <div className="form-group">
          <label htmlFor="title">Case Title *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="e.g., Employee Vs ABC Corporation"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'Arial',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
            required
          />
        </div>

        {/* Case Type */}
        <div className="form-group">
          <label htmlFor="caseType">Case Type *</label>
          <select
            id="caseType"
            name="caseType"
            value={formData.caseType}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          >
            {caseTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        {/* Case Summary */}
        <div className="form-group">
          <label htmlFor="summary">Case Summary *</label>
          <textarea
            id="summary"
            name="summary"
            value={formData.summary}
            onChange={handleChange}
            placeholder="Provide a detailed summary of the case..."
            rows="6"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'Arial',
              fontSize: '1rem',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
            required
          />
          <small style={{ color: '#999' }}>
            {formData.summary.length} characters
          </small>
        </div>

        {/* Court */}
        <div className="form-group">
          <label htmlFor="court">Court Name</label>
          <input
            type="text"
            id="court"
            name="court"
            value={formData.court}
            onChange={handleChange}
            placeholder="e.g., Supreme Court of Sri Lanka"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'Arial',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {/* Year */}
        <div className="form-group">
          <label htmlFor="year">Year</label>
          <input
            type="number"
            id="year"
            name="year"
            value={formData.year}
            onChange={handleChange}
            min="1950"
            max={new Date().getFullYear()}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'Arial',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {/* Key Points */}
        <div className="form-group">
          <label htmlFor="keyPoints">Key Points (comma-separated)</label>
          <textarea
            id="keyPoints"
            name="keyPoints"
            value={formData.keyPoints}
            onChange={handleChange}
            placeholder="e.g., wage dispute, dismissal without notice, violation of labor law"
            rows="3"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'Arial',
              fontSize: '1rem',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
          />
          <small style={{ color: '#999' }}>
            Enter key points separated by commas
          </small>
        </div>

        {/* Outcome */}
        <div className="form-group">
          <label htmlFor="outcome">Case Outcome</label>
          <select
            id="outcome"
            name="outcome"
            value={formData.outcome}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          >
            <option value="Pending">Pending</option>
            <option value="Granted">Granted</option>
            <option value="Dismissed">Dismissed</option>
            <option value="Settled">Settled</option>
            <option value="Appealed">Appealed</option>
            <option value="Withdrawn">Withdrawn</option>
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '1rem',
            background: loading ? '#ccc' : '#1e3c72',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginTop: '1.5rem'
          }}
        >
          {loading ? '⏳ Adding Case...' : '➕ Add Case to Database'}
        </button>
      </form>

      {/* Info Box */}
      <div style={{
        background: '#f0f4f8',
        padding: '1.5rem',
        borderRadius: '8px',
        marginTop: '2rem',
        borderLeft: '4px solid #1e3c72'
      }}>
        <h4>💡 Tips for Adding Cases</h4>
        <ul>
          <li>✓ Use clear, descriptive titles</li>
          <li>✓ Include detailed summaries with key facts</li>
          <li>✓ Add relevant key points for better matching</li>
          <li>✓ Select the correct case type</li>
          <li>✓ Include court name for reference</li>
          <li>✓ Mark case outcome if known</li>
        </ul>
        <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
          Cases added to the database will be used for similarity matching when users search for similar cases.
        </p>
      </div>
    </div>
  );
}

export default AddCase;
