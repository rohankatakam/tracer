'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

interface GitHubIssueImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GitHubIssueImportModal: React.FC<GitHubIssueImportModalProps> = ({
  isOpen,
  onClose,
}) => {
  const router = useRouter();
  const [issueUrl, setIssueUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleImport = async () => {
    // Reset error state
    setError(null);
    
    // Validate URL
    if (!issueUrl || issueUrl.trim() === '') {
      setError('Please enter a GitHub issue URL');
      return;
    }

    // Normalize the URL by trimming whitespace
    const normalizedUrl = issueUrl.trim();

    // Check if it's a valid GitHub issue URL
    const githubUrlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+\/issues\/\d+$/;
    if (!githubUrlPattern.test(normalizedUrl)) {
      setError('Please enter a valid GitHub issue URL (https://github.com/owner/repo/issues/number)');
      return;
    }

    try {
      setIsLoading(true);
      
      // Parse the URL to extract owner, repo, and issue number for validation
      const urlParts = normalizedUrl.match(/https:\/\/github\.com\/([^\/]+)\/([^\/]+)\/issues\/(\d+)/);
      if (!urlParts || urlParts.length !== 4) {
        throw new Error('Invalid GitHub issue URL format');
      }
      
      // Double-check our URL is well-formed before proceeding
      const [_, owner, repo, issueNumber] = urlParts;
      if (!owner || !repo || !issueNumber) {
        throw new Error('Missing required GitHub issue information');
      }
      
      // Encode the URL to pass it safely in the redirect
      const encodedUrl = encodeURIComponent(normalizedUrl);
      
      // Close the modal and redirect to the create bug page with the GitHub issue URL as a parameter
      onClose();
      router.push(`/bugs/create?githubIssueUrl=${encodedUrl}`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process GitHub issue URL');
      setIsLoading(false);
      console.error('Error importing GitHub issue:', err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Import GitHub Issue</h2>
        
        <p className="text-gray-600 mb-4">
          Enter the URL of the GitHub issue you want to import.
        </p>
        
        <div className="mb-4">
          <Input
            label="GitHub Issue URL"
            value={issueUrl}
            onChange={(e) => setIssueUrl(e.target.value)}
            placeholder="https://github.com/owner/repo/issues/123"
          />
          {error && (
            <p className="text-red-500 text-sm mt-1">{error}</p>
          )}
        </div>
        
        <div className="flex justify-end space-x-3">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleImport}
            isLoading={isLoading}
            disabled={isLoading}
          >
            Import Issue
          </Button>
        </div>
      </div>
    </div>
  );
};
