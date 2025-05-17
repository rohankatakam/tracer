'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAllBugs } from '../../hooks/useBugs';
import { BugCard } from '../../components/bugs/BugCard';
import { SeverityLevel } from '../../types/bug';

export default function BugListPage() {
  const { bugs, isLoading, error } = useAllBugs();
  const [severityFilter, setSeverityFilter] = useState<SeverityLevel | 'all'>('all');

  const filteredBugs = bugs.filter(bug => 
    severityFilter === 'all' || bug.severity === severityFilter
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">All Bugs</h1>
        <Link href="/bugs/create" className="btn btn-primary">
          Report New Bug
        </Link>
      </div>

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
          {Object.values(SeverityLevel).map((severity) => (
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
            <BugCard key={bug.id} bug={bug} />
          ))}
        </div>
      )}
    </div>
  );
}
