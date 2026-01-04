import React from 'react';
import './About.css';

function About() {
  return (
    <div className="container">
      <div className="about-page">
        <h2>ℹ️ About Us</h2>
        
        <div className="about-content">
          <section className="about-section">
            <h3>Welcome to Legal Case Analyzer</h3>
            <p>
              Legal Case Analyzer is an innovative AI-powered platform designed to revolutionize 
              how legal professionals analyze, manage, and understand complex legal documents and cases.
            </p>
          </section>

          <section className="about-section">
            <h3>Our Mission</h3>
            <p>
              To empower legal professionals with advanced tools that leverage artificial intelligence 
              and machine learning to streamline legal research, case analysis, and compliance auditing. 
              We aim to make legal work more efficient, accurate, and accessible.
            </p>
          </section>

          <section className="about-section">
            <h3>Key Features</h3>
            <div className="features-list">
              <div className="feature">
                <h4>⚖️ Similar Cases Analyzer</h4>
                <p>Find and analyze legally similar cases using advanced AI-powered matching algorithms.</p>
              </div>
              <div className="feature">
                <h4>📋 Civil Compliance Auditor</h4>
                <p>Automatically audit cases for compliance violations and receive actionable recommendations.</p>
              </div>
              <div className="feature">
                <h4>📊 Structured View</h4>
                <p>Convert unstructured case documents into organized, easy-to-understand structured formats.</p>
              </div>
              <div className="feature">
                <h4>📈 Argument Strength Score</h4>
                <p>Evaluate the strength of your legal arguments with detailed analysis and improvement suggestions.</p>
              </div>
            </div>
          </section>

          <section className="about-section">
            <h3>Technology Stack</h3>
            <p>
              Built on the MERN stack (MongoDB, Express, React, Node.js), our platform combines 
              modern web technologies with advanced AI/ML algorithms to deliver powerful legal analysis capabilities.
            </p>
          </section>

          <section className="about-section">
            <h3>Why Choose Us?</h3>
            <ul className="reasons-list">
              <li>💡 Advanced AI-powered legal analysis</li>
              <li>⚡ Fast and efficient case processing</li>
              <li>📱 Mobile-responsive design</li>
              <li>🔒 Secure and confidential handling of legal documents</li>
              <li>📊 Comprehensive reporting and insights</li>
              <li>🤝 Dedicated support for legal professionals</li>
            </ul>
          </section>

          <section className="about-section">
            <h3>Contact Us</h3>
            <div className="contact-info">
              <p><strong>Email:</strong> info@legalcaseanalyzer.com</p>
              <p><strong>Phone:</strong> +1 (555) 123-4567</p>
              <p><strong>Address:</strong> 123 Legal Street, Justice City, JC 12345</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default About;
