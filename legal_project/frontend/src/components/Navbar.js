import React from 'react';

function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark">
      <div className="container-fluid">
        <a className="navbar-brand" href="/">
          ⚖️ Legal Case Analyzer
        </a>
        <span className="navbar-text text-white">
          Intelligent Legal Document Search & Classification
        </span>
      </div>
    </nav>
  );
}

export default Navbar;
