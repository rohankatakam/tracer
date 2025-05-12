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

function BugListPage() {
  return (
    <div>
      <div className="page-header">
        <h1>Outstanding Bugs</h1>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #ddd', textAlign: 'left' }}>
            <th style={{ padding: '8px' }}>Bug ID</th>
            <th style={{ padding: '8px' }}>Title</th>
            <th style={{ padding: '8px' }}>Severity</th>
            <th style={{ padding: '8px' }}>Status</th>
            <th style={{ padding: '8px' }}>Product</th>
          </tr>
        </thead>
        <tbody>
          {dummyBugs.map((bug) => (
            <tr key={bug.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '8px' }}>
                <Link to={`/bugs/${bug.id}`}>{bug.id}</Link>
              </td>
              <td style={{ padding: '8px' }}>{bug.title}</td>
              <td style={{ padding: '8px' }}>{bug.severity}</td>
              <td style={{ padding: '8px' }}>{bug.status}</td>
              <td style={{ padding: '8px' }}>{bug.product}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default BugListPage; 