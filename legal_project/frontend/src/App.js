import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import SimilarCases from './pages/SimilarCases';
import ComplianceAuditor from './pages/ComplianceAuditor';
import StructuredView from './pages/StructuredView';
import ArgumentScore from './pages/ArgumentScore';
import About from './pages/About';
import './App.css';

function App() {
  return (
    <Router>
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/similar-cases" element={<SimilarCases />} />
          <Route path="/compliance" element={<ComplianceAuditor />} />
          <Route path="/structured-view" element={<StructuredView />} />
          <Route path="/argument-score" element={<ArgumentScore />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>&copy; 2026 Legal Case Analyzer. All rights reserved.</p>
      </footer>
    </Router>
  );
}

export default App;
