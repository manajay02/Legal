import React, { useState, useEffect } from 'react';
import '../styles/DownloadActsPage.css';

function DownloadActsPage({ onBack, onReAnalyze }) {
  const [availableActs, setAvailableActs] = useState([]);
  const [loadingActs, setLoadingActs] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Act categories
  const categories = [
    { id: 'all', name: 'All Acts', icon: '📚' },
    { id: 'employment', name: 'Employment Law', icon: '👔' },
    { id: 'property', name: 'Property & Rental', icon: '🏠' },
    { id: 'finance', name: 'Finance & Banking', icon: '💰' },
    { id: 'consumer', name: 'Consumer Protection', icon: '🛡️' },
    { id: 'general', name: 'General Law', icon: '📄' },
  ];

  // Categorize acts based on their names
  const categorizeAct = (filename) => {
    const lower = filename.toLowerCase();
    if (lower.includes('shop') || lower.includes('office') || lower.includes('epf') || 
        lower.includes('etf') || lower.includes('employment') || lower.includes('maternity') ||
        lower.includes('gratuity') || lower.includes('wage') || lower.includes('industrial') ||
        lower.includes('workmen') || lower.includes('trade') || lower.includes('labour')) {
      return 'employment';
    }
    if (lower.includes('rent') || lower.includes('property') || lower.includes('land') || 
        lower.includes('registration') || lower.includes('apartment') || lower.includes('tenancy')) {
      return 'property';
    }
    if (lower.includes('finance') || lower.includes('bank') || lower.includes('leasing') || 
        lower.includes('credit') || lower.includes('loan') || lower.includes('monetary')) {
      return 'finance';
    }
    if (lower.includes('consumer') || lower.includes('protection') || lower.includes('fair')) {
      return 'consumer';
    }
    return 'general';
  };

  // Fetch available acts PDFs on component mount
  useEffect(() => {
    const fetchActs = async () => {
      try {
        const response = await fetch('http://localhost:8000/acts/list');
        const data = await response.json();
        const actsWithCategories = (data.acts || []).map(act => ({
          filename: act,
          category: categorizeAct(act),
          displayName: getActDisplayName(act)
        }));
        setAvailableActs(actsWithCategories);
      } catch (error) {
        console.error('Error fetching acts:', error);
        setAvailableActs([]);
      } finally {
        setLoadingActs(false);
      }
    };
    fetchActs();
  }, []);

  // Function to download an act PDF
  const handleDownloadAct = (filename) => {
    const downloadUrl = `http://localhost:8000/acts/download/${encodeURIComponent(filename)}`;
    window.open(downloadUrl, '_blank');
  };

  // Get display name for act (remove .pdf extension and format)
  const getActDisplayName = (filename) => {
    return filename.replace(/\.pdf$/i, '').replace(/_/g, ' ').replace(/-/g, ' ');
  };

  // Filter acts based on search and category
  const filteredActs = availableActs.filter(act => {
    const matchesSearch = act.displayName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || act.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Group acts by category for the grouped view
  const groupedActs = filteredActs.reduce((acc, act) => {
    if (!acc[act.category]) {
      acc[act.category] = [];
    }
    acc[act.category].push(act);
    return acc;
  }, {});

  return (
    <div className="download-acts-page">
      {/* Page Header */}
      <div className="page-header">
        <div className="header-left">
          <button className="back-btn" onClick={onBack}>
            <span className="back-arrow">←</span>
            <span>Back</span>
          </button>
        </div>
        <div className="header-right">
          <button className="reanalyze-btn" onClick={onReAnalyze}>
            <span className="btn-icon">📤</span>
            <span>Analyze Document</span>
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="acts-hero">
        <div className="hero-content">
          <div className="hero-icon">📚</div>
          <h1 className="page-title">Sri Lankan Legal Acts & Regulations</h1>
          <p className="page-subtitle">
            Download official legislation documents for reference. These acts form the legal basis 
            for our compliance analysis.
          </p>
        </div>
      </div>

      {/* Search and Filter Section */}
      <div className="search-filter-section">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search acts by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button className="clear-search" onClick={() => setSearchTerm('')}>✕</button>
          )}
        </div>
        
        <div className="category-filters">
          {categories.map(cat => (
            <button
              key={cat.id}
              className={`category-btn ${selectedCategory === cat.id ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat.id)}
            >
              <span className="cat-icon">{cat.icon}</span>
              <span className="cat-name">{cat.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Acts Count */}
      <div className="acts-count highlighted">
        <span className="count-number">{filteredActs.length}</span>
        <span className="count-label">
          {filteredActs.length === 1 ? 'Act' : 'Acts'} Available
          {selectedCategory !== 'all' && ` in ${categories.find(c => c.id === selectedCategory)?.name}`}
        </span>
      </div>

      {/* Acts Grid */}
      <div className="acts-content">
        {loadingActs ? (
          <div className="acts-loading">
            <div className="loading-spinner"></div>
            <p>Loading available acts...</p>
          </div>
        ) : filteredActs.length > 0 ? (
          <div className="acts-grid">
            {filteredActs.map((act, index) => (
              <div key={index} className="act-card">
                <div className="act-header">
                  <div className="act-icon">📄</div>
                  <div className="act-category">
                    <span className="category-icon">
                      {categories.find(c => c.id === act.category)?.icon || '📄'}
                    </span>
                    <span className="category-name">
                      {categories.find(c => c.id === act.category)?.name || 'General'}
                    </span>
                  </div>
                </div>
                <div className="act-body">
                  <h4 className="act-name">{act.displayName}</h4>
                  <span className="act-type">PDF Document</span>
                </div>
                <div className="act-footer">
                  <button 
                    className="download-btn"
                    onClick={() => handleDownloadAct(act.filename)}
                    title={`Download ${act.filename}`}
                  >
                   
                    <span>Download PDF</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-acts">
            <div className="no-acts-icon">📭</div>
            <h3>No Acts Found</h3>
            {searchTerm ? (
              <p>No acts match your search "{searchTerm}". Try a different search term.</p>
            ) : selectedCategory !== 'all' ? (
              <p>No acts available in this category. Try selecting "All Acts".</p>
            ) : (
              <p>No legislation documents are currently available for download.</p>
            )}
            {(searchTerm || selectedCategory !== 'all') && (
              <button 
                className="reset-btn"
                onClick={() => { setSearchTerm(''); setSelectedCategory('all'); }}
              >
                Show All Acts
              </button>
            )}
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="info-section">
        <div className="info-card">
          <div className="info-icon">ℹ️</div>
          <div className="info-content">
            <h4>About These Documents</h4>
            <p>
              These are official Sri Lankan legislative documents used as reference for compliance analysis. 
              The documents are sourced from official government publications and are provided for informational purposes only.
              For legal advice, please consult a qualified legal professional.
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button className="action-btn secondary" onClick={onBack}>
          <span className="btn-icon">←</span>
          Back
        </button>
        <button className="action-btn primary" onClick={onReAnalyze}>
          <span className="btn-icon">📤</span>
          Analyze a Document
        </button>
      </div>
    </div>
  );
}

export default DownloadActsPage;
