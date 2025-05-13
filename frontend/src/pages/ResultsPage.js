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

    const reproductionStatusStyle = {
        padding: '15px 20px',
        borderRadius: '6px',
        marginBottom: '25px',
        border: '1px solid',
        backgroundColor: simulatedReproduced ? '#d4edda' : '#f8d7da',
        borderColor: simulatedReproduced ? '#c3e6cb' : '#f5c6cb',
        color: simulatedReproduced ? '#155724' : '#721c24',
    };

    return (
        <div>
            <div className="page-header">
                <h1>Tracer Results: Bug {bugId}</h1>
            </div>

            <section style={reproductionStatusStyle}>
                <h2 style={{ marginTop: 0, marginBottom: 0, fontSize: '1.4em' }}>
                     Reproduction Status: {simulatedReproduced ? 'Successfully Reproduced' : 'Failed to Reproduce'}
                 </h2>
            </section>

            <div className="card">
                <h3>Result Categorization</h3>
                <label htmlFor="resultCode">Result Code: </label>
                <select id="resultCode" value={resultCode} onChange={(e) => setResultCode(e.target.value)} style={{ marginLeft: '10px', padding: '5px', minWidth: '250px' }}>
                    {Object.entries(resultCodes).map(([code, description]) => (
                        <option key={code} value={code}>{description} ({code})</option>
                    ))}
                </select>
                <p style={{ fontSize: '0.9em', color: '#6c757d', marginTop: '5px' }}>*LLM-generated suggestion, editable by user.*</p>
            </div>

            {!simulatedReproduced && moreInfoRequest && (
                <div className="card">
                    <h3 style={{ color: '#856404' }}>Request for More Information (from Customer)</h3>
                    <p>{moreInfoRequest}</p>
                </div>
            )}

             {!simulatedReproduced && stuckInfo && (
                <div className="card">
                    <h3 style={{ color: '#721c24' }}>Request for Input (from User)</h3>
                    <p>{stuckInfo}</p>
                </div>
            )}

            {simulatedReproduced && proposedSolution && (
                 <div className="card">
                    <h3>Proposed Solution / Analysis</h3>
                    <p style={{ fontSize: '0.95em', color: '#6c757d', marginBottom: '15px' }}>The following analysis is based on successful reproduction and simulated log/code cross-referencing:</p>
                    <pre>
                        {proposedSolution}
                    </pre>
                </div>
            )}

            <div className="card">
                <h3>Suggested Status Change</h3>
                 <label htmlFor="statusSuggest">Status: </label>
                <select id="statusSuggest" value={suggestedStatus} onChange={(e) => setSuggestedStatus(e.target.value)} style={{ marginLeft: '10px', padding: '5px', minWidth: '200px' }}>
                    {statusSuggestions.map((status) => (
                        <option key={status} value={status}>{status}</option>
                    ))}
                </select>
                 <p style={{ fontSize: '0.9em', color: '#6c757d', marginTop: '5px' }}>*LLM-generated suggestion, editable by user.*</p>
            </div>

             <button onClick={handleReproduceAgain} style={{ marginTop: '10px', padding: '12px 25px', fontSize: '1.1em', backgroundColor: '#6c757d' }}>
                Reproduce Again
            </button>

        </div>
    );
}

export default ResultsPage; 