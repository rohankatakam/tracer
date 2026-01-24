import React, { useEffect, useState } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import './ResultsPage.css'; // Assuming you have or will create this CSS file

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
    const location = useLocation(); // To get state passed from navigation
    const navigate = useNavigate(); // For "Reproduce Again" type buttons
    const queryParams = new URLSearchParams(location.search);

    const isDemo = queryParams.get('demo') === 'true';
    const reproduced = queryParams.get('reproduced') === 'true';
    
    // State for API-fetched results (if not in demo mode)
    const [apiResults, setApiResults] = useState(null);
    const [isLoading, setIsLoading] = useState(!isDemo); // Don't load if demo
    const [error, setError] = useState(null);

    // For demo mode, get logs and title from location state
    const demoLogsFromState = isDemo ? location.state?.demoLogs : null;
    const demoBugTitle = isDemo ? location.state?.bugTitle : "Demo Bug";

    // State for editable fields / API results
    const [resultCode, setResultCode] = useState('');
    const [suggestedStatus, setSuggestedStatus] = useState('');
    const [analysisText, setAnalysisText] = useState(''); // For proposed solution / analysis
    const [errorFromApi, setErrorFromApi] = useState(null);
    const [isLoadingApi, setIsLoadingApi] = useState(!isDemo);

    useEffect(() => {
        if (isDemo && reproduced) {
            setResultCode('BUG_REPRODUCED_CONSISTENT');
            setSuggestedStatus('Validated');
            setAnalysisText(
`The X/Twitter social share link bug was successfully reproduced. 

Observations:
- Clicking the 'X' icon on the product page (e.g., for 'DNK Yellow Shoes') attempts to navigate to a Twitter sharing URL.
- The navigation fails with a DNS error (specifically, the page shows an error like "Server Not Found" or "Hmm. We're having trouble finding that site").
- The URL in the address bar shows a typo: "https://twitter.cointent/..." instead of "https://twitter.com/intent/...".

Root Cause:
The issue is a typo in the constructed URL for the X/Twitter sharing functionality. The domain is incorrectly specified as "twitter.cointent".

Recommended Fix:
1. Locate the code responsible for generating the social media sharing links (likely in a frontend component or a backend template).
2. Correct the typo in the Twitter sharing URL from "twitter.cointent" to "twitter.com/intent".
3. Test the corrected link across multiple products to ensure proper redirection to the X/Twitter sharing interface.
`);
            setIsLoadingApi(false);
        } else if (!isDemo && bugId) {
            setIsLoadingApi(true);
            // TODO: Replace with actual API call to fetch results for bugId
            console.log(`Non-demo: Would fetch results for ${bugId}`);
            setTimeout(() => { // Simulating API call
                if (reproduced) {
                    setResultCode('BUG_REPRODUCED_CONSISTENT'); // Example
                    setSuggestedStatus('Validated');
                    setAnalysisText(`Bug ${bugId} was reproduced. Further API-driven analysis would go here.`);
                } else {
                    setResultCode('CANNOT_REPRODUCE_STEPS');
                    setSuggestedStatus('Needs More Info');
                    setAnalysisText(`Could not reproduce bug ${bugId}. Steps may be unclear or environment specific.`);
                }
                setIsLoadingApi(false);
            }, 1000);
        }
    }, [bugId, isDemo, reproduced, location.state]);

    const handleReproduceAgain = () => {
        const path = isDemo ? '/hardcoded-task-flow' : `/tracer/${bugId}/run`;
        navigate(path);
    };

    if (isLoading && !isDemo) {
        return <div className="results-container loading"><h2>Loading Results for {bugId}...</h2></div>;
    }

    if (error && !isDemo) {
        return <div className="results-container error"><h2>Error loading results: {error}</h2></div>;
    }

    return (
        <div className="results-container">
            <h1 className="results-title {isDemo ? 'demo-title' : ''}">
                {isDemo ? `DEMO RESULT: ${demoBugTitle}` : `Results for Bug: ${bugId}`}
            </h1>
            <div className={`status-banner ${reproduced ? 'success' : 'failure'}`}>
                {reproduced ? "Bug Successfully Reproduced!" : (isDemo ? "Bug Not Reproduced (Demo Configuration)" : "Bug Not Reproduced")}
            </div>

            <div className="results-section card">
                <h3>Result Categorization</h3>
                <label htmlFor="resultCode">Result Code: </label>
                <select id="resultCode" value={resultCode} onChange={(e) => setResultCode(e.target.value)} style={{ marginLeft: '10px', padding: '5px', minWidth: '250px' }}>
                    {Object.entries(resultCodes).map(([code, description]) => (
                        <option key={code} value={code}>{description} ({code})</option>
                    ))}
                </select>
            </div>

            <div className="results-section card">
                <h3>Suggested Status</h3>
                <label htmlFor="statusSuggest">Status: </label>
                <select id="statusSuggest" value={suggestedStatus} onChange={(e) => setSuggestedStatus(e.target.value)} style={{ marginLeft: '10px', padding: '5px', minWidth: '200px' }}>
                    {statusSuggestions.map((status) => (
                        <option key={status} value={status}>{status}</option>
                    ))}
                </select>
            </div>

            <div className="results-section card">
                <h3>Analysis & Proposed Solution</h3>
                <textarea 
                    value={analysisText} 
                    onChange={(e) => setAnalysisText(e.target.value)} 
                    rows={15} 
                    style={{width: '98%', padding: '10px', fontFamily:'monospace', whiteSpace: 'pre-wrap'}}
                    placeholder={isDemo && reproduced ? "Details of the reproduced demo bug..." : "Enter analysis or solution here..."}
                />
            </div>

            {isDemo && demoLogsFromState && (
                <div className="results-section">
                    <h2>Full Demo Agent Logs:</h2>
                    <div className="log-display-results">
                        {demoLogsFromState.map((logBlock, index) => (
                            <pre key={index} className="log-entry-results">{logBlock}</pre>
                        ))}
                    </div>
                </div>
            )}
            
            <button onClick={handleReproduceAgain} style={{ marginTop: '20px', padding: '10px 18px' }}>
                {isDemo ? "Run Demo Again" : "Reproduce Again"}
            </button>
            <Link to={isDemo ? "/bugs" : `/bugs/${bugId}`} className="back-link" style={{marginLeft: '10px'}}>
                {isDemo ? "Back to Bug List" : "Back to Bug Detail"}
            </Link>
            {!isDemo && <Link to="/bugs" className="back-link" style={{marginLeft: '10px'}}>Back to Bug List</Link>}
        </div>
    );
}

export default ResultsPage; 