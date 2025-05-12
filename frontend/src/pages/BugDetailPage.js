import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// --- Dummy Data (could be fetched based on bugId) ---
const dummyBugDetails = {
  'SV-20250411': {
    id: 'SV-20250411',
    title: 'JSON Tampering Exploit in Purchase Order Approval Workflow',
    severity: 'Critical',
    status: 'Open',
    product: 'ProcureWave v3.2.7',
    reportedBy: 'Acme Industries',
    reportedDate: '2025-04-11',
    description: "A security vulnerability allows malicious actors to tamper with JSON requests in the purchase order approval workflow. By modifying the 'total_amount' and 'approval_status' fields, attackers can bypass financial approval limits and self-approve purchase orders for amounts exceeding their authorization. This exploit also allows for access to restricted cost centers.",
    stepsToReproduce: [
      'Log in to ProcureWave.',
      "Navigate to 'Purchase Orders'.",
      "Select 'Create PO Request'.",
      "Fill in standard PO fields: Vendor, Items, Cost Center.",
      "Configure Burp Suite (or similar proxy) to intercept POST requests to the /api/purchase_orders endpoint.",
      "Submit the PO. In the intercepted request, modify the JSON body:",
      "  - Change 'total_amount' from original value (e.g., 49.99) to a high value (e.g., 49999.99).",
      "  - Add/Change 'approval_status' to 'CFO_APPROVED'.",
      "  - Set 'cost_center_id' to a restricted one (e.g., 'FIN-2023-EXEC').",
      "Forward the modified JSON to ProcureWave.",
      "Observe server response (expected 200 OK, PO #XYZ created).",
      "Navigate to PO Dashboard and verify PO #XYZ shows as 'CFO_APPROVED' with the inflated amount."
    ],
    expectedBehavior: "The system should validate the 'total_amount' against user approval limits and prevent unauthorized changes to 'approval_status' and 'cost_center_id'. The request should be rejected or flagged for review.",
    actualBehavior: "The system accepts the tampered JSON, creating a PO with an inflated amount, an unauthorized approval status, and potentially an incorrect cost center. The server responds with 200 OK.",
    securityImpact: "Bypass of financial approval thresholds (normal limit: $5,000); Self-approval of purchase orders requiring CFO signature; Access to restricted cost centers outside user's department.",
    attachments: [
      { name: 'ProcureWave_Vulnerability_Diagram.png', type: 'image', url: '/images/ProcureWave_Security_Vulnerability.png' }, // Using the provided image path
      { name: 'exploit_poc.mp4', type: 'video', url: '#' }, // Placeholder video
      { name: 'burp_request_log.txt', type: 'log', url: '#' }
    ],
    categorization: {
      type: 'Security Vulnerability',
      area: 'Purchase Order Module',
      CWE: 'CWE-502: Deserialization of Untrusted Data' // Example CWE
    }
  },
  // ... add other bug details if needed for testing navigation
  'UI-20250320': {
    id: 'UI-20250320',
    title: 'User Profile Image Upload Fails with Large Files',
    severity: 'High',
    // ... (rest of the fields for this bug)
    description: 'Users are unable to upload profile pictures larger than 5MB. The UI shows a generic error message.',
    attachments: [],
    stepsToReproduce: ['Try to upload an image > 5MB as profile picture'],
  }
};
// --- End Dummy Data ---

function BugDetailPage() {
  const { bugId } = useParams();
  const navigate = useNavigate();
  const bug = dummyBugDetails[bugId] || dummyBugDetails['SV-20250411']; // Fallback to default if ID not found

  if (!bug) {
    return <div><h2>Bug Not Found</h2><p>The requested bug ID does not exist.</p></div>;
  }

  const handleRunTracer = () => {
    navigate(`/tracer/${bugId}/run`);
  };

  return (
    <div>
      <div className="page-header">
        <h1>Bug Detail: {bug.id}</h1>
      </div>
      
      <h2>{bug.title}</h2>
      <p><strong>Severity:</strong> {bug.severity} | <strong>Status:</strong> {bug.status || 'Open'}</p>
      <p><strong>Product:</strong> {bug.product} | <strong>Reported By:</strong> {bug.reportedBy || 'N/A'} on {bug.reportedDate || 'N/A'}</p>

      <section style={{ marginTop: '20px', marginBottom: '20px' }}>
        <h3>Description</h3>
        <p>{bug.description}</p>
      </section>

      {bug.stepsToReproduce && bug.stepsToReproduce.length > 0 && (
        <section style={{ marginTop: '20px', marginBottom: '20px' }}>
          <h3>Steps to Reproduce</h3>
          <ol>
            {bug.stepsToReproduce.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {bug.expectedBehavior && (
         <section style={{ marginTop: '20px', marginBottom: '20px' }}>
          <h3>Expected Behavior</h3>
          <p>{bug.expectedBehavior}</p>
        </section>
      )}
      {bug.actualBehavior && (
         <section style={{ marginTop: '20px', marginBottom: '20px' }}>
          <h3>Actual Behavior</h3>
          <p>{bug.actualBehavior}</p>
        </section>
      )}
      {bug.securityImpact && (
         <section style={{ marginTop: '20px', marginBottom: '20px' }}>
          <h3>Security Impact</h3>
          <p>{bug.securityImpact}</p>
        </section>
      )}

      {bug.attachments && bug.attachments.length > 0 && (
        <section style={{ marginTop: '20px', marginBottom: '20px' }}>
          <h3>Attachments / Customer Documentation</h3>
          <ul>
            {bug.attachments.map((att, index) => (
              <li key={index}>
                {att.type === 'image' ? (
                  <img src={att.url} alt={att.name} style={{ maxWidth: '400px', maxHeight: '300px', display: 'block', margin: '10px 0' }} />
                ) : (
                  <a href={att.url} target="_blank" rel="noopener noreferrer">{att.name}</a>
                )}
                ({att.type})
              </li>
            ))}
          </ul>
        </section>
      )}

      {bug.categorization && (
        <section style={{ marginTop: '20px', marginBottom: '20px' }}>
          <h3>Categorization</h3>
          <p><strong>Type:</strong> {bug.categorization.type}</p>
          <p><strong>Area:</strong> {bug.categorization.area}</p>
          {bug.categorization.CWE && <p><strong>CWE:</strong> {bug.categorization.CWE}</p>}
        </section>
      )}

      <button onClick={handleRunTracer} style={{ marginTop: '20px', padding: '12px 25px', fontSize: '1.2em' }}>
        Run Tracer
      </button>
    </div>
  );
}

export default BugDetailPage; 