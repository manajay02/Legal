import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import SimilarCases from './pages/SimilarCases';
import CaseLibrary from './pages/CaseLibrary';
import CaseDetails from './pages/CaseDetails';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/similar" element={<SimilarCases />} />
            <Route path="/library" element={<CaseLibrary />} />
            <Route path="/case/:id" element={<CaseDetails />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
