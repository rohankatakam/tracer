'use client';

import React, { useState, useEffect } from 'react';
import { Comment } from '../../types/comment';
import { Attachment } from '../../types/bug';
import { commentAPI } from '../../services/api-client';
import { CommentItem } from './CommentItem';
import { CommentForm } from './CommentForm';

interface CommentSectionProps {
  bugId: string;
  attachments?: Attachment[];
}

export const CommentSection: React.FC<CommentSectionProps> = ({ 
  bugId,
  attachments = []
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Create a map of attachment ID to attachment object for quick lookups
  const attachmentMap = attachments.reduce((map, attachment) => {
    map[attachment.attachment_id] = attachment;
    return map;
  }, {} as Record<string, Attachment>);
  
  const fetchComments = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Log bug ID for debugging
      console.log(`Fetching comments for bug ID: ${bugId}`);
      
      // Normalize bug ID by removing any hyphens and converting to lowercase
      // This step is just for logging purposes to help diagnose any issues
      const normalizedBugId = bugId.replace(/-/g, '').toLowerCase();
      console.log(`Normalized bug ID: ${normalizedBugId}`);
      
      const fetchedComments = await commentAPI.getBugComments(bugId);
      setComments(fetchedComments);
    } catch (err: any) {
      console.error('Error fetching comments:', err);
      
      // Enhanced error message with more details
      if (err?.message?.includes('404') || err?.message?.includes('not found')) {
        setError(`Bug ID "${bugId}" not found. This could be due to a URL formatting issue.`);
      } else if (err?.message?.includes('500')) {
        setError('Server error when loading comments. The backend may be experiencing issues.');
      } else {
        setError(`Failed to load comments: ${err?.message || 'Unknown error'}`);
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  // Load comments on initial render
  useEffect(() => {
    fetchComments();
  }, [bugId]);
  
  return (
    <div className="mt-6">
      <h2 className="text-lg font-medium mb-4">Comments</h2>
      
      {isLoading ? (
        <div className="text-center py-6">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-gray-500">Loading comments...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          <p>{error}</p>
          <div className="mt-3">
            <button 
              onClick={fetchComments}
              className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded mr-2"
            >
              Try again
            </button>
            <a 
              href="/bugs"
              className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded inline-block"
            >
              Return to bug list
            </a>
          </div>
          {error.includes('not found') && (
            <p className="mt-2 text-sm text-red-600">
              <strong>Tip:</strong> Try navigating back to the bug list and selecting the bug again.
            </p>
          )}
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-6 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No comments yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map(comment => (
            <CommentItem
              key={comment.comment_id}
              comment={comment}
              attachmentMap={attachmentMap}
              onUpdate={fetchComments}
              onDelete={fetchComments}
            />
          ))}
        </div>
      )}
      
      {/* Add comment form */}
      <div className="mt-6">
        <CommentForm 
          bugId={bugId} 
          attachments={attachments}
          onCommentAdded={fetchComments}
        />
      </div>
    </div>
  );
};
