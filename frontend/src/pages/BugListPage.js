import React from 'react';
import { Link } from 'react-router-dom';

// --- Dummy Data ---
const dummyBugs = [
  {
    id: 'SV-20250411',
    title: 'JSON Tampering Exploit in Purchase Order Approval Workflow',
    severity: 'Critical',
    status: 'Open',
    product: 'ProcureWave v3.2.7',
    reportedBy: 'Acme Industries'
  },
  {
    id: 'UI-20250320',
    title: 'User Profile Image Upload Fails with Large Files',
    severity: 'High',
    status: 'Open',
    product: 'ConnectSphere v1.5.0',
    reportedBy: 'Beta Testers Inc.'
  },
  {
    id: 'DB-20250401',
    title: 'Race Condition During Account Balance Update',
    severity: 'Medium',
    status: 'In Progress',
    product: 'FinanceCore v2.1',
    reportedBy: 'Internal QA'
  },
  {
    id: 'FE-20250415',
    title: 'Incorrect Currency Formatting on Checkout Page',
    severity: 'Low',
    status: 'Open',
    product: 'ShopEasy v4.0.1',
    reportedBy: 'Customer Support'
  }
];
// --- End Dummy Data ---

const getSeverityStyle = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return { color: '#dc3545', fontWeight: 'bold' }; // Red
    case 'high':
      return { color: '#fd7e14' }; // Orange
    case 'medium':
      return { color: '#ffc107' }; // Yellow
    case 'low':
      return { color: '#17a2b8' }; // Cyan/Blue
    default:
      return {};
  }
};

function BugListPage() {
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
          {dummyBugs.map((bug) => (
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