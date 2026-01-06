import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './Home.css';

function Home() {
  const [stats, setStats] = useState({ totalCases: 0, categories: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/cases/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home">
      <section className="hero">
        <h1>Legal Case Analyzer</h1>
        <p>Analyze legal documents and find similar cases from our database</p>
        <div className="hero-buttons">
          <Link to="/similar" className="btn btn-primary">Find Similar Cases</Link>
          <Link to="/library" className="btn btn-secondary">Browse Library</Link>
        </div>
      </section>

      <section className="stats-section">
        <h2>Database Statistics</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="stats-grid">
            <div className="stat-card total">
              <h3>{stats.totalCases}</h3>
              <p>Total Cases</p>
            </div>
            {stats.categories.map(cat => (
              <div key={cat.name} className="stat-card">
                <h3>{cat.count}</h3>
                <p>{cat.name}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="features">
        <h2>Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <span className="feature-icon">📄</span>
            <h3>Upload Documents</h3>
            <p>Upload PDF, DOCX, or TXT files for analysis</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🔍</span>
            <h3>Find Similar Cases</h3>
            <p>AI-powered similarity matching</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">📚</span>
            <h3>Case Library</h3>
            <p>Browse and search legal cases</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
