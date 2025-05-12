import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Navigate
} from 'react-router-dom';
import BugListPage from './pages/BugListPage';
import BugDetailPage from './pages/BugDetailPage';
import TracerPage from './pages/TracerPage';
import ResultsPage from './pages/ResultsPage';
import './App.css'; // App-specific styles

function App() {
  return (
    <Router>
      <div className="App">
        <nav>
          <ul>
            {/* Basic navigation for context, might remove later */}
            <li><Link to="/bugs">Bug List</Link></li>
          </ul>
        </nav>
        <main className="container">
          <Routes>
            <Route path="/" element={<Navigate to="/bugs" replace />} />
            <Route path="/bugs" element={<BugListPage />} />
            <Route path="/bugs/:bugId" element={<BugDetailPage />} />
            <Route path="/tracer/:bugId/run" element={<TracerPage />} />
            <Route path="/tracer/:bugId/results" element={<ResultsPage />} />
            {/* Add a 404 or default route later if needed */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 