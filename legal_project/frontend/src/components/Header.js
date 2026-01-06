import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

function Header() {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  return (
    <header className="header">
      <nav className="navbar">
        <div className="logo">
          <h1>⚖️ Legal Case Analyzer</h1>
        </div>
        
        <button className="mobile-menu-toggle" onClick={toggleMenu}>
          <span></span>
          <span></span>
          <span></span>
        </button>

        <ul className={`nav-menu ${isOpen ? 'active' : ''}`}>
          <li><Link to="/" onClick={closeMenu}>🏠 Home</Link></li>
          <li><Link to="/similar-cases" onClick={closeMenu}>⚖️ Similar Cases</Link></li>
          <li><Link to="/compliance" onClick={closeMenu}>📋 Compliance Auditor</Link></li>
          <li><Link to="/structured-view" onClick={closeMenu}>📊 Structured View</Link></li>
          <li><Link to="/argument-score" onClick={closeMenu}>📈 Argument Score</Link></li>
          <li className="dropdown">
            <span>📚 Cases</span>
            <ul className="dropdown-menu">
              <li><Link to="/add-case" onClick={closeMenu}>➕ Add Case</Link></li>
              <li><Link to="/cases-database" onClick={closeMenu}>📂 View Database</Link></li>
            </ul>
          </li>
          <li><Link to="/about" onClick={closeMenu}>ℹ️ About Us</Link></li>
        </ul>
      </nav>
    </header>
  );
}

export default Header;
