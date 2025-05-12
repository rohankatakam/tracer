import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';

// --- Dummy Data & Logic ---
const resultCodes = {
    'VULN_CONFIRMED_EXPLOIT': 'Vulnerability Confirmed - Exploitable',
    'VULN_CONFIRMED_NO_EXPLOIT': 'Vulnerability Confirmed - Not Exploitable',
    'BUG_REPRODUCED_CONSISTENT': 'Bug Reproduced - Consistent',
    'BUG_REPRODUCED_INTERMITTENT': 'Bug Reproduced - Intermittent',
    'CANNOT_REPRODUCE_CONFIG': 'Cannot Reproduce - Configuration Issue Suspected',
    'CANNOT_REPRODUCE_ENV': 'Cannot Reproduce - Environment Issue Suspected',
    'CANNOT_REPRODUCE_STEPS': 'Cannot Reproduce - Steps Unclear/Incorrect',
    'AGENT_FAILURE_TOOL': 'Agent Failure - Tool Error',
    'AGENT_FAILURE_NAVIGATION': 'Agent Failure - Navigation Error',
    'NEEDS_INFO_CUSTOMER': 'Needs More Information - Customer',
    'NEEDS_INFO_USER': 'Needs More Information - User Input Required'
    // Add ~40 more specific codes here if needed
};

const statusSuggestions = [
    'Triaged',
    'Validated',
    'Needs Reproduction',
    'Needs More Info',
    'Closed - Cannot Reproduce',
    'Closed - Works as Designed'
];
// --- End Dummy Data & Logic ---

function ResultsPage() {
    const { bugId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    // Get reproduction status from query params (passed from TracerPage simulation)
    const queryParams = new URLSearchParams(location.search);
    const simulatedReproduced = queryParams.get('reproduced') === 'true';

    // State for editable fields
    const [resultCode, setResultCode] = useState(simulatedReproduced ? 'VULN_CONFIRMED_EXPLOIT' : 'CANNOT_REPRODUCE_STEPS');
    const [suggestedStatus, setSuggestedStatus] = useState(simulatedReproduced ? 'Validated' : 'Needs Reproduction');
    const [proposedSolution, setProposedSolution] = useState('');
    const [moreInfoRequest, setMoreInfoRequest] = useState('');
    const [stuckInfo, setStuckInfo] = useState(''); // Info if agent got stuck

    // Simulate generating content based on result
    useEffect(() => {
        if (simulatedReproduced) {
            setProposedSolution(
`Based on the successful reproduction and analysis of logs (simulated), the vulnerability appears to stem from insufficient input validation in the 'api/purchase_orders' endpoint handler.

Recommended Fix:
1. Implement strict validation on the server-side for 'total_amount' against user-specific approval limits before processing the request.
2. Ensure 'approval_status' cannot be overridden by the client request; it should only be set by the backend approval logic.
3. Validate 'cost_center_id' against the user's allowed cost centers.

Relevant Code Files (Simulated):
- 'src/server/controllers/purchase_order_controller.py' (line 152)
- 'src/server/middleware/auth_middleware.py' (line 88)
`
            );
            setMoreInfoRequest(''); // Clear if reproduced
            setStuckInfo(''); // Clear if reproduced
        } else {
            setProposedSolution(''); // Clear if not reproduced
            setMoreInfoRequest('The reproduction steps provided were unclear around Step 4 (JSON modification). Could the customer please provide the exact JSON payload they used before and after modification? A HAR file capture would be ideal.');
            setStuckInfo('The agent simulation got stuck during Step 3 (Proxy Setup). Manual intervention might be required to confirm proxy configuration.'); // Example if stuck
        }
    }, [simulatedReproduced]);

    const handleReproduceAgain = () => {
        // Navigate back to the Tracer page to run again
        navigate(`/tracer/${bugId}/run`);
    };

    return (
        <div>
            <div className="page-header">
                <h1>Tracer Results: Bug {bugId}</h1>
            </div>

            <section style={{ marginBottom: '25px', padding: '15px', border: `2px solid ${simulatedReproduced ? '#2ecc71' : '#e74c3c'}` }}>
                <h2>Reproduction Status: {simulatedReproduced ? 'Successfully Reproduced' : 'Failed to Reproduce'}</h2>
            </section>

            <section style={{ marginBottom: '20px' }}>
                <h3>Result Categorization</h3>
                <label htmlFor="resultCode">Result Code: </label>
                <select id="resultCode" value={resultCode} onChange={(e) => setResultCode(e.target.value)} style={{ marginLeft: '10px', padding: '5px' }}>
                    {Object.entries(resultCodes).map(([code, description]) => (
                        <option key={code} value={code}>{description} ({code})</option>
                    ))}
                </select>
                <p style={{ fontSize: '0.9em', color: '#555' }}>*LLM-generated suggestion, editable by user.*</p>
            </section>

            {/* Display dynamic sections based on outcome */} 
            {!simulatedReproduced && moreInfoRequest && (
                <section style={{ marginBottom: '20px', border: '1px solid #f1c40f', padding: '10px' }}>
                    <h3>Request for More Information (from Customer)</h3>
                    <p>{moreInfoRequest}</p>
                </section>
            )}

             {!simulatedReproduced && stuckInfo && (
                <section style={{ marginBottom: '20px', border: '1px solid #e74c3c', padding: '10px' }}>
                    <h3>Request for Input (from User)</h3>
                    <p>{stuckInfo}</p>
                </section>
            )}

            {simulatedReproduced && proposedSolution && (
                <section style={{ marginBottom: '20px' }}>
                    <h3>Proposed Solution / Analysis</h3>
                    <p>The following analysis is based on successful reproduction and simulated log/code cross-referencing:</p>
                    <pre style={{ backgroundColor: '#eee', padding: '10px', borderRadius: '5px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {proposedSolution}
                    </pre>
                </section>
            )}

            <section style={{ marginBottom: '20px' }}>
                <h3>Suggested Status Change</h3>
                 <label htmlFor="statusSuggest">Status: </label>
                <select id="statusSuggest" value={suggestedStatus} onChange={(e) => setSuggestedStatus(e.target.value)} style={{ marginLeft: '10px', padding: '5px' }}>
                    {statusSuggestions.map((status) => (
                        <option key={status} value={status}>{status}</option>
                    ))}
                </select>
                 <p style={{ fontSize: '0.9em', color: '#555' }}>*LLM-generated suggestion, editable by user.*</p>
            </section>

             <button onClick={handleReproduceAgain} style={{ marginTop: '20px', padding: '12px 25px', fontSize: '1.2em', backgroundColor: '#e67e22' }}>
                Reproduce Again
            </button>

        </div>
    );
}

export default ResultsPage; 