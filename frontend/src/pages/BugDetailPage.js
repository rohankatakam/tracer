import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// Public examples mirrored from academybugs_bug_reports.json.
const demoBugDetails = {
  academybugs_currency_freeze_01: {
    id: 'academybugs_currency_freeze_01',
    title: 'Website freezes when changing currency on product page',
    severity: 'Medium',
    status: 'Ready for reproduction',
    product: 'AcademyBugs.com',
    source: 'Public demo fixture',
    targetUrl: 'https://academybugs.com/find-bugs/',
    description: 'Changing the currency on a product detail page may leave the website unresponsive.',
    stepsToReproduce: [
      "Navigate to the public 'Find Bugs' page.",
      'Open the first available product.',
      'Locate and open the currency selector.',
      'Choose a currency different from the current selection.',
      'Observe whether the page remains responsive.'
    ],
    expectedBehavior: 'The page should apply the new currency and remain responsive.',
    reportedBehavior: 'The public demo report says the interface freezes after the currency changes.'
  },
  academybugs_twitter_share_nxdomain_01: {
    id: 'academybugs_twitter_share_nxdomain_01',
    title: 'X/Twitter share link leads to a DNS error',
    severity: 'Low',
    status: 'Ready for reproduction',
    product: 'AcademyBugs.com',
    source: 'Public demo fixture',
    targetUrl: 'https://academybugs.com/find-bugs/',
    description: 'The social share link may open an unreachable host instead of a sharing page.',
    stepsToReproduce: [
      "Navigate to the public 'Find Bugs' page.",
      'Open a product.',
      'Click the X/Twitter sharing icon.',
      'Record the destination and any browser error.'
    ],
    expectedBehavior: 'A valid sharing page should open.',
    reportedBehavior: 'The public demo report describes a DNS_PROBE_FINISHED_NXDOMAIN error.'
  },
  academybugs_hot_item_perpetual_load_01: {
    id: 'academybugs_hot_item_perpetual_load_01',
    title: "Clicking 'HOT ITEM' leads to perpetual loading",
    severity: 'Medium',
    status: 'Ready for reproduction',
    product: 'AcademyBugs.com',
    source: 'Public demo fixture',
    targetUrl: 'https://academybugs.com/find-bugs/',
    description: "The 'HOT ITEM' link may leave the page in a loading state that never resolves.",
    stepsToReproduce: [
      "Navigate to the public 'Find Bugs' page.",
      'Open a product.',
      "Click the 'HOT ITEM' image or link.",
      'Observe the page and browser loading indicator.'
    ],
    expectedBehavior: 'The requested content should load or fail with a clear error.',
    reportedBehavior: 'The public demo report describes a perpetual loading state.'
  }
};

function BugDetailPage() {
  const { bugId } = useParams();
  const navigate = useNavigate();
  const bug = demoBugDetails[bugId];

  if (!bug) {
    return <div><h2>Bug Not Found</h2><p>The requested demo bug does not exist.</p></div>;
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
      <p><strong>Severity:</strong> {bug.severity} | <strong>Status:</strong> {bug.status}</p>
      <p><strong>Application:</strong> {bug.product} | <strong>Source:</strong> {bug.source}</p>
      <p><strong>Authorized demo target:</strong> <a href={bug.targetUrl}>{bug.targetUrl}</a></p>

      <section style={{ marginTop: '20px', marginBottom: '20px' }}>
        <h3>Description</h3>
        <p>{bug.description}</p>
      </section>

      <section style={{ marginTop: '20px', marginBottom: '20px' }}>
        <h3>Steps to Reproduce</h3>
        <ol>
          {bug.stepsToReproduce.map((step, index) => <li key={index}>{step}</li>)}
        </ol>
      </section>

      <section style={{ marginTop: '20px', marginBottom: '20px' }}>
        <h3>Expected Behavior</h3>
        <p>{bug.expectedBehavior}</p>
      </section>

      <section style={{ marginTop: '20px', marginBottom: '20px' }}>
        <h3>Reported Behavior</h3>
        <p>{bug.reportedBehavior}</p>
      </section>

      <p><em>This frontend is a static simulation. Running it does not control the Python agent.</em></p>

      <button onClick={handleRunTracer} style={{ marginTop: '20px', padding: '12px 25px', fontSize: '1.2em' }}>
        Open Tracer Simulation
      </button>
    </div>
  );
}

export default BugDetailPage;
