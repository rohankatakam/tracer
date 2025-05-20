'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAllBugs } from '../../hooks/useBugs';
import { BugCard } from '../../components/bugs/BugCard';
import { GitHubIssueImportModal } from '../../components/bugs/GitHubIssueImportModal';
import { Button } from '../../components/ui/Button';
import { BaseSeverity, Bug, BaseTypeBug, MozillaBug, ChromiumBug, OracleBug, GitHubIssueBug } from '../../types/bug';

export default function BugListPage() {
  const { bugs, isLoading, error } = useAllBugs();
  const [severityFilter, setSeverityFilter] = useState<BaseSeverity | 'all'>('all');
  const [isGitHubImportModalOpen, setIsGitHubImportModalOpen] = useState(false);

  const filteredBugs = bugs.filter(bug => {
    if (severityFilter === 'all') return true;
    
    // Handle different bug schema types
    switch (bug.schema_type) {
      case 'base':
        return (bug as BaseTypeBug).severity === severityFilter;
      case 'mozilla':
        // For Mozilla bugs, try to match BaseSeverity names to MozillaSeverity
        // This is approximate as the severities don't exactly match
        return (bug as MozillaBug).mozilla_severity?.toLowerCase().includes(severityFilter.toLowerCase());
      case 'chromium':
        // For Chromium bugs, check if they have a matching priority instead
        return false; // We could implement a more sophisticated mapping here
      case 'oracle':
        // For Oracle bugs, check if they have a matching severity
        return (bug as OracleBug).oracle_severity?.toLowerCase() === severityFilter.toLowerCase();
      case 'github': // Updated from 'github_issue' to match backend expectations
        // For GitHub Issues, we could map labels to severity levels
        // For now, return true to show all GitHub issues regardless of severity filter
        return true;
      default:
        return false;
    }
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">All Bugs</h1>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={() => setIsGitHubImportModalOpen(true)}
          >
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            Import from GitHub
          </Button>
          <Link href="/bugs/create">
            <Button>
              Report New Bug
            </Button>
          </Link>
        </div>
      </div>
      
      {/* GitHub Issue Import Modal */}
      <GitHubIssueImportModal 
        isOpen={isGitHubImportModalOpen} 
        onClose={() => setIsGitHubImportModalOpen(false)}
      />

      <div className="mb-6">
        <label className="form-label">Filter by severity:</label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSeverityFilter('all')}
            className={`px-3 py-1 text-sm rounded-full ${
              severityFilter === 'all' 
                ? 'bg-gray-800 text-white' 
                : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            }`}
          >
            All
          </button>
          {Object.values(BaseSeverity).map((severity) => (
            <button
              key={severity}
              onClick={() => setSeverityFilter(severity)}
              className={`px-3 py-1 text-sm rounded-full ${
                severityFilter === severity
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
            >
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-gray-500">Loading bugs...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="underline text-red-700 mt-2"
          >
            Try again
          </button>
        </div>
      ) : filteredBugs.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-gray-500">
            {bugs.length === 0 
              ? 'No bugs reported yet. Be the first to report a bug!' 
              : 'No bugs match the selected filter.'}
          </p>
          {bugs.length === 0 && (
            <Link href="/bugs/create" className="btn btn-primary mt-4">
              Report New Bug
            </Link>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredBugs.map(bug => (
            <BugCard key={bug.bug_id} bug={bug} />
          ))}
        </div>
      )}
    </div>
  );
}
