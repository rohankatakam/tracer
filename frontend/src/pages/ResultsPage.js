import React, { useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';

const resultCodes = {
  REVIEW_REQUIRED: 'Trace complete - human review required',
  REPRODUCED: 'Reviewer confirmed reproduction',
  NOT_REPRODUCED: 'Reviewer did not reproduce',
  NEEDS_MORE_INFO: 'More report detail required',
  AGENT_FAILURE: 'Agent or browser failure'
};

const statusSuggestions = [
  'Needs review',
  'Validated',
  'Needs more information',
  'Cannot reproduce'
];

function ResultsPage() {
  const { bugId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const simulationComplete = queryParams.get('simulation') === 'complete';

  const [resultCode, setResultCode] = useState('REVIEW_REQUIRED');
  const [suggestedStatus, setSuggestedStatus] = useState('Needs review');

  const handleReproduceAgain = () => {
    navigate(`/tracer/${bugId}/run`);
  };

  return (
    <div>
      <div className="page-header">
        <h1>Tracer Review: {bugId}</h1>
      </div>

      <section className="card">
        <h2>{simulationComplete ? 'Static trace simulation complete' : 'No completed simulation found'}</h2>
        <p>
          This UI does not contain evidence from a live agent run. A reviewer must inspect
          real screenshots and execution logs before choosing a reproduction outcome.
        </p>
      </section>

      <div className="card">
        <h3>Reviewer outcome</h3>
        <label htmlFor="resultCode">Result: </label>
        <select
          id="resultCode"
          value={resultCode}
          onChange={(event) => setResultCode(event.target.value)}
          style={{ marginLeft: '10px', padding: '5px', minWidth: '300px' }}
        >
          {Object.entries(resultCodes).map(([code, description]) => (
            <option key={code} value={code}>{description} ({code})</option>
          ))}
        </select>
      </div>

      <div className="card">
        <h3>Suggested issue status</h3>
        <label htmlFor="statusSuggest">Status: </label>
        <select
          id="statusSuggest"
          value={suggestedStatus}
          onChange={(event) => setSuggestedStatus(event.target.value)}
          style={{ marginLeft: '10px', padding: '5px', minWidth: '220px' }}
        >
          {statusSuggestions.map((status) => <option key={status}>{status}</option>)}
        </select>
        <p style={{ fontSize: '0.9em', color: '#6c757d' }}>
          The selection is local UI state and is not written to an issue tracker.
        </p>
      </div>

      <button onClick={handleReproduceAgain} style={{ marginTop: '10px', padding: '12px 25px', fontSize: '1.1em' }}>
        Run Simulation Again
      </button>
    </div>
  );
}

export default ResultsPage;
