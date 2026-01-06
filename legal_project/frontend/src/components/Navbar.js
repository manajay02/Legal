import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">⚖️ Legal Case Analyzer</Link>
      </div>
      <ul className="navbar-links">
        <li className={location.pathname === '/' ? 'active' : ''}>
          <Link to="/">Home</Link>
        </li>
        <li className={location.pathname === '/similar' ? 'active' : ''}>
          <Link to="/similar">Find Similar Cases</Link>
        </li>
        <li className={location.pathname === '/library' ? 'active' : ''}>
          <Link to="/library">Case Library</Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
