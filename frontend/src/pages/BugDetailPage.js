import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { demoBugId } from './demoData'; // Import demoBugId to compare

// --- Dummy Data (could be fetched based on bugId) ---
// const dummyBugDetails = { ... }; // REMOVE THIS
// --- End Dummy Data ---

function BugDetailPage() {
  const { bugId } = useParams();
  const navigate = useNavigate();
  
  // State for bug details, loading, and error
  const [bugDetails, setBugDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // The ID of the bug that has the special hardcoded demo task flow
  const bugIdForSpecialDemo = demoBugId.replace('_demo', ''); // Should be 'academybugs_twitter_share_nxdomain_01'

  // Fetch bug details from API on component mount or when bugId changes
  useEffect(() => {
    const fetchBugDetails = async () => {
      if (!bugId) return;
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:5001/api/bugs/${bugId}`);
        if (!response.ok) {
          const errorData = await response.json(); // Attempt to get error message from API
          throw new Error(errorData.description || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBugDetails(data); // Set the fetched bug details
      } catch (e) {
        setError(e.message);
        setBugDetails(null);
        console.error(`Failed to fetch bug details for ${bugId}:`, e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchBugDetails();
  }, [bugId]);

  // const bug = dummyBugDetails[bugId] || dummyBugDetails['SV-20250411']; // REMOVE THIS LINE

  if (isLoading) {
    return <div><h2>Loading Bug Details for {bugId}...</h2></div>;
  }
  
  if (error) {
    return (
      <div>
        <h2>Error Loading Bug: {bugId}</h2>
        <p style={{ color: 'red' }}>{error}</p>
        <button onClick={() => navigate('/bugs')}>Back to Bug List</button>
      </div>
    );
  }

  // More robust check: ensure bug and bug.bug_metadata exist before proceeding
  if (!bugDetails || !bugDetails.bug_metadata) { 
    return (
        <div>
            <h2>Bug Data Not Available</h2>
            <p>The bug details for {bugId} could not be loaded or are incomplete.</p>
            <button onClick={() => navigate('/bugs')}>Back to Bug List</button>
        </div>
    );
  }

  const handleRunAction = () => {
    if (bugId === bugIdForSpecialDemo) {
      // For the specific Twitter bug, navigate to the new task-flow route
      navigate('/task-flow'); 
    } else {
      // For all other bugs, go to the live tracer page
      navigate(`/tracer/${bugId}/run`);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Bug Detail: {bugDetails.bug_metadata.bug_id || bugId}</h1> 
      </div>
      
      <div className="card" style={{ marginBottom: '25px' }}> {/* Main details card */}
        <h2>{bugDetails.bug_metadata.bug_title || 'No Title'}</h2>
        <p>
          <strong>Severity:</strong> <span className={`badge ${getSeverityBadgeClass(bugDetails.bug_metadata.severity?.description || bugDetails.bug_metadata.severity)}`}>{bugDetails.bug_metadata.severity?.description || bugDetails.bug_metadata.severity || 'N/A'}</span> |
          <strong> Status:</strong> <span className={`badge ${getStatusBadgeClass(bugDetails.bug_metadata.status?.description || bugDetails.bug_metadata.status)}`}>{bugDetails.bug_metadata.status?.description || bugDetails.bug_metadata.status || 'N/A'}</span>
        </p>
        <p>
          <strong>Product:</strong> {bugDetails.bug_metadata.product?.name || 'N/A'} |
          <strong> Reported By:</strong> {bugDetails.bug_metadata.customer?.name || bugDetails.bug_metadata.reportedBy || 'N/A'} 
          {bugDetails.bug_metadata.reportedDate && `on ${bugDetails.bug_metadata.reportedDate}`}
        </p>
      </div>

      {bugDetails.bug_content?.description && (
        <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Description</h3>
          <p>{bugDetails.bug_content.description}</p>
        </div>
      )}

      {/* Steps to Reproduce Section */}
      {bugDetails.bug_content?.steps_to_reproduce && Array.isArray(bugDetails.bug_content.steps_to_reproduce) && bugDetails.bug_content.steps_to_reproduce.length > 0 && (
        <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Steps to Reproduce</h3>
          <ol style={{ paddingLeft: '20px' }}>
            {bugDetails.bug_content.steps_to_reproduce.map((step, index) => (
              <li key={index} style={{ marginBottom: '5px' }}>{step}</li>
            ))}
          </ol>
        </div>
      )}
      {bugDetails.bug_content?.steps_to_reproduce && !Array.isArray(bugDetails.bug_content.steps_to_reproduce) && (
        <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Steps to Reproduce (Raw)</h3>
          {typeof bugDetails.bug_content.steps_to_reproduce === 'string' ? (
            <pre style={{ whiteSpace: 'pre-wrap' }}>{bugDetails.bug_content.steps_to_reproduce}</pre>
          ) : (
            <p><em>Steps to reproduce are present but not in the expected array format.</em></p>
          )}
        </div>
      )}

      {bugDetails.bug_content?.expected_outcome && (
         <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Expected Behavior</h3>
          <p>{bugDetails.bug_content.expected_outcome}</p>
        </div>
      )}
      {bugDetails.bug_content?.actual_outcome && ( 
         <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Actual Behavior</h3>
          <p>{bugDetails.bug_content.actual_outcome}</p>
        </div>
      )}
      {bugDetails.bug_metadata.security_impact && ( 
         <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Security Impact</h3>
          <p>{bugDetails.bug_metadata.security_impact}</p>
        </div>
      )}

      {bugDetails.attachments && bugDetails.attachments.length > 0 && (
        <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Attachments / Customer Documentation</h3>
          <ul style={{ listStyle: 'none', paddingLeft: '0'}}>
            {bugDetails.attachments.map((att, index) => (
              <li key={index} style={{ marginBottom: '10px' }}>
                {att.type === 'image' ? (
                  <img src={att.url} alt={att.name} style={{ maxWidth: '400px', maxHeight: '300px', display: 'block', margin: '10px 0' }} />
                ) : (
                  <a href={att.url} target="_blank" rel="noopener noreferrer">{att.name}</a>
                )}
                ({att.type})
              </li>
            ))}
          </ul>
        </div>
      )}

      {bugDetails.bug_metadata.categorization && (
        <div className="card" style={{ marginBottom: '25px' }}>
          <h3>Categorization</h3>
          <p><strong>Type:</strong> {bugDetails.bug_metadata.categorization.type}</p>
          <p><strong>Area:</strong> {bugDetails.bug_metadata.categorization.area}</p>
          {bugDetails.bug_metadata.categorization.CWE && <p><strong>CWE:</strong> {bugDetails.bug_metadata.categorization.CWE}</p>}
        </div>
      )}

      <div className="bug-actions">
        <button onClick={handleRunAction} className="action-button">
          {bugId === bugIdForSpecialDemo ? 'Run Demo Task Flow' : 'Run Tracer (Live)'}
        </button>
      </div>

      <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#f4f4f4', padding: '15px', borderRadius: '4px' }}>
        {JSON.stringify(bugDetails, null, 2)}
      </pre>
      <Link to="/bugs" className="back-link" style={{marginTop: '20px'}}>Back to Bug List</Link>
    </div>
  );
}

// Helper functions for badges (need to be defined or imported in this file too if not global)
const getSeverityBadgeClass = (severity) => {
  const severityLower = severity?.toLowerCase();
  switch (severityLower) {
    case 'critical': return 'badge-critical';
    case 'high': return 'badge-high';
    case 'medium': return 'badge-medium';
    case 'low': return 'badge-low';
    default: return 'badge-neutral';
  }
};

const getStatusBadgeClass = (status) => {
  // Add more sophisticated status mapping if needed
  const statusLower = status?.toLowerCase();
  if (statusLower === 'open') return 'badge-high';
  if (statusLower === 'new') return 'badge-info';
  if (statusLower === 'closed') return 'badge-success';
  return 'badge-status'; 
};

export default BugDetailPage; 