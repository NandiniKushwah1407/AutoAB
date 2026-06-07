import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ExperimentsList from './pages/ExperimentsList';
import CreateExperiment from './pages/CreateExperiment';
import ExperimentDetail from './pages/ExperimentDetail';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="header">
          <div className="header-content">
            <Link to="/" className="logo">VariantIQ</Link>
            <nav className="nav">
              <Link to="/">Experiments</Link>
              <Link to="/create">Create New</Link>
            </nav>
          </div>
        </header>
        
        <Routes>
          <Route path="/" element={<ExperimentsList />} />
          <Route path="/create" element={<CreateExperiment />} />
          <Route path="/experiment/:id" element={<ExperimentDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
