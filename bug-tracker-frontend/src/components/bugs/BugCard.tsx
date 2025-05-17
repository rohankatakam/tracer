import React from 'react';
import Link from 'next/link';
import { Bug, BaseSeverity, BaseTypeBug, MozillaBug, ChromiumBug, OracleBug, BugSchemaType } from '../../types/bug';

interface BugCardProps {
  bug: Bug;
}

export const BugCard: React.FC<BugCardProps> = ({ bug }) => {
  const getSeverityBadgeColor = (severity: string) => {
    const severityLower = severity.toLowerCase();
    
    if (severityLower.includes('low') || severityLower.includes('minor') || severityLower.includes('trivial')) {
      return 'bg-blue-100 text-blue-800';
    } else if (severityLower.includes('medium') || severityLower.includes('normal')) {
      return 'bg-yellow-100 text-yellow-800';
    } else if (severityLower.includes('high') || severityLower.includes('major')) {
      return 'bg-orange-100 text-orange-800';
    } else if (severityLower.includes('critical') || severityLower.includes('blocker')) {
      return 'bg-red-100 text-red-800';
    } else {
      return 'bg-gray-100 text-gray-800';
    }
  };
  
  // Get the appropriate severity text based on bug schema type
  const getSeverityText = (bug: Bug): string => {
    switch (bug.schema_type) {
      case BugSchemaType.BASE:
        return (bug as BaseTypeBug).severity || 'Unknown';
      case BugSchemaType.MOZILLA:
        return (bug as MozillaBug).mozilla_severity || 'Unknown';
      case BugSchemaType.CHROMIUM:
        // Chromium doesn't have severity but has priority
        return (bug as ChromiumBug).chromium_priority || 'Unknown';
      case BugSchemaType.ORACLE:
        return (bug as OracleBug).oracle_severity || 'Unknown';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-4 border-l-4 border-primary hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <h3 className="text-lg font-medium text-gray-900 mb-1 truncate">
          <Link 
            href={`/bugs/${encodeURIComponent(bug.bug_id)}`} 
            className="hover:text-primary"
          >
            {bug.title}
          </Link>
        </h3>
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadgeColor(getSeverityText(bug))}`}>
          {getSeverityText(bug).charAt(0).toUpperCase() + getSeverityText(bug).slice(1)}
        </span>
      </div>
      
      <p className="text-sm text-gray-500 mt-1 line-clamp-2">{bug.description}</p>
      
      <div className="mt-3 flex justify-between items-center text-xs text-gray-500">
        <div>Reported by: {bug.reporter}</div>
        <div>
          {new Date(bug.created_at).toLocaleDateString()} 
          {bug.attachments && bug.attachments.length > 0 && (
            <span className="ml-2 inline-flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              {bug.attachments.length}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
