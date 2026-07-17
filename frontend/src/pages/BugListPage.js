import React from 'react';
import { Link } from 'react-router-dom';

// Public examples mirrored from academybugs_bug_reports.json.
const demoBugs = [
  {
    id: 'academybugs_currency_freeze_01',
    title: 'Website freezes when changing currency on product page',
    severity: 'Medium',
    status: 'Ready for reproduction',
    product: 'AcademyBugs.com'
  },
  {
    id: 'academybugs_twitter_share_nxdomain_01',
    title: 'X/Twitter share link leads to a DNS error',
    severity: 'Low',
    status: 'Ready for reproduction',
    product: 'AcademyBugs.com'
  },
  {
    id: 'academybugs_hot_item_perpetual_load_01',
    title: "Clicking 'HOT ITEM' leads to perpetual loading",
    severity: 'Medium',
    status: 'Ready for reproduction',
    product: 'AcademyBugs.com'
  }
];

const getSeverityStyle = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high':
      return { color: '#fd7e14' };
    case 'medium':
      return { color: '#856404', fontWeight: 'bold' };
    case 'low':
      return { color: '#17a2b8' };
    default:
      return {};
  }
};

function BugListPage() {
  return (
    <div>
      <div className="page-header">
        <h1>Public Demo Bugs</h1>
        <p>Static examples for illustrating Tracer's review flow.</p>
      </div>
      <table>
        <thead>
          <tr>
            <th>Bug ID</th>
            <th>Title</th>
            <th>Severity</th>
            <th>Status</th>
            <th>Application</th>
          </tr>
        </thead>
        <tbody>
          {demoBugs.map((bug) => (
            <tr key={bug.id}>
              <td>
                <Link to={`/bugs/${bug.id}`}>{bug.id}</Link>
              </td>
              <td>{bug.title}</td>
              <td style={getSeverityStyle(bug.severity)}>{bug.severity}</td>
              <td>{bug.status}</td>
              <td>{bug.product}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default BugListPage;
