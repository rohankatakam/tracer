import { useState, useEffect } from 'react';
import { Bug } from '../types/bug';
import { bugAPI, attachmentAPI } from '../services/api-client';

export function useAllBugs() {
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBugs = async () => {
      try {
        setIsLoading(true);
        const data = await bugAPI.getAll();
        setBugs(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch bugs. Please try again later.');
        console.error('Error fetching bugs:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchBugs();
  }, []);

  return { bugs, isLoading, error };
}

export function useBugById(bugId: string | null) {
  const [bug, setBug] = useState<Bug | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bugId) return;

    const fetchBug = async () => {
      try {
        setIsLoading(true);
        const data = await bugAPI.getById(bugId);
        
        // Fetch attachments if there are any
        if (data.attachment_count && data.attachment_count > 0) {
          try {
            const attachments = await attachmentAPI.getBugAttachments(bugId);
            // Add attachments to the bug data
            data.attachments = attachments;
          } catch (attachmentErr) {
            console.error(`Error fetching attachments for bug ${bugId}:`, attachmentErr);
            // Continue with the bug data even if attachments failed to load
            data.attachments = [];
          }
        } else {
          data.attachments = [];
        }
        
        setBug(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch bug details. Please try again later.');
        console.error(`Error fetching bug with ID ${bugId}:`, err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchBug();
  }, [bugId]);

  return { bug, isLoading, error };
}
