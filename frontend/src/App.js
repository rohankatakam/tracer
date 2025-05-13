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
            <li>
              <Link to="/bugs" className="nav-brand">
                <img src="/images/tracer-logo.png" alt="Tracer Logo" className="nav-logo" />
                {/* Removed text link from here to avoid redundancy */}
              </Link>
            </li>
            {/* Optional: Add other main navigation items here as separate <li> elements */}
             <li><Link to="/bugs">Bugs</Link></li>
          </ul>
        </nav>
        <main className="container"> {/* Keep .container for main content padding/max-width */}
          <Routes>
            <Route path="/" element={<Navigate to="/bugs" replace />} />
            <Route path="/bugs" element={<BugListPage />} />
            <Route path="/bugs/:bugId" element={<BugDetailPage />} />
            <Route path="/tracer/:bugId/run" element={<TracerPage />} />
            <Route path="/tracer/:bugId/results" element={<ResultsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 