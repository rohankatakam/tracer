import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// --- Dummy Data ---
// const dummyBugs = [ ... ]; // REMOVE THIS
// --- End Dummy Data ---

// Function to get badge class based on severity
const getSeverityBadgeClass = (severity) => {
  const severityLower = severity?.toLowerCase();
  switch (severityLower) {
    case 'critical':
      return 'badge-critical';
    case 'high':
      return 'badge-high';
    case 'medium':
      return 'badge-medium';
    case 'low':
      return 'badge-low';
    default:
      return 'badge-neutral';
  }
};

// Function to get badge class for status (can be expanded)
const getStatusBadgeClass = (status) => {
  // Simple for now, can be expanded with more status types and colors
  return 'badge-status'; 
};

function BugListPage() {
  // State for bugs, loading, and errors
  const [bugs, setBugs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch bugs from API on component mount
  useEffect(() => {
    const fetchBugs = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Use the new API endpoint
        const response = await fetch('http://localhost:5001/api/bugs'); 
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBugs(data); // Set the fetched bugs
      } catch (e) {
        setError(e.message);
        setBugs([]); // Clear bugs on error
        console.error("Failed to fetch bugs:", e); // Log error
      } finally {
        setIsLoading(false);
      }
    };

    fetchBugs();
  }, []); // Empty dependency array means this runs once on mount

  if (isLoading) {
    return (
      <div>
        <div className="page-header">
          <h1>Outstanding Bugs</h1>
        </div>
        <p>Loading bugs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h1>Outstanding Bugs</h1>
        </div>
        <p style={{ color: 'red' }}>Error loading bugs: {error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Outstanding Bugs</h1>
      </div>
      <table>
        <thead>
          <tr>
            <th>Bug ID</th>
            <th>Title</th>
            <th>Severity</th>
            <th>Status</th>
            <th>Product</th>
          </tr>
        </thead>
        <tbody>
          {bugs.length === 0 ? (
            <tr>
              <td colSpan="5">No bugs found.</td>
            </tr>
          ) : (
            bugs.map((bug) => (
              <tr key={bug.id}>
                <td>
                  <Link to={`/bugs/${bug.id}`}>{bug.id}</Link>
                </td>
                <td>{bug.title}</td>
                <td>
                  <span className={`badge ${getSeverityBadgeClass(bug.severity)}`}>
                    {bug.severity}
                  </span>
                </td>
                <td>
                  <span className={`badge ${getStatusBadgeClass(bug.status?.description)}`}>
                    {bug.status?.description || 'N/A'}
                  </span>
                </td>
                <td>{bug.product}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default BugListPage; 