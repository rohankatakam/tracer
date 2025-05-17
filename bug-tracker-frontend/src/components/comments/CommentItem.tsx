'use client';

import React, { useState } from 'react';
import { Comment } from '../../types/comment';
import { Button } from '../ui/Button';
import { commentAPI } from '../../services/api-client';
import { formatDistanceToNow } from 'date-fns';

interface CommentItemProps {
  comment: Comment;
  attachmentMap: Record<string, any>;
  onUpdate: () => void;
  onDelete: () => void;
}

export const CommentItem: React.FC<CommentItemProps> = ({ 
  comment, 
  attachmentMap, 
  onUpdate, 
  onDelete 
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.text);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Format the comment timestamp
  const timestampDisplay = comment.timestamp 
    ? formatDistanceToNow(new Date(comment.timestamp), { addSuffix: true })
    : 'recently';
  
  const handleUpdate = async () => {
    if (!editText.trim()) {
      setError('Comment text cannot be empty');
      return;
    }
    
    try {
      setIsSaving(true);
      setError(null);
      
      await commentAPI.updateComment(comment.comment_id, {
        text: editText.trim()
      });
      
      onUpdate();
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating comment:', err);
      setError('Failed to update comment');
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this comment?')) {
      try {
        setIsDeleting(true);
        await commentAPI.deleteComment(comment.comment_id);
        onDelete();
      } catch (err) {
        console.error('Error deleting comment:', err);
        setError('Failed to delete comment');
        setIsDeleting(false);
      }
    }
  };
  
  const renderAttachmentReference = (attachmentId: string) => {
    const attachment = attachmentMap[attachmentId];
    if (!attachment) return attachmentId;
    
    return (
      <span 
        key={attachmentId}
        className="inline-flex items-center px-2 py-1 mx-1 bg-blue-50 text-blue-700 rounded text-xs"
        title={`${attachment.filename} (${attachment.file_type})`}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
        </svg>
        {attachment.filename}
      </span>
    );
  };
  
  // Process the comment text to highlight attachment references
  const renderCommentText = () => {
    if (!comment.attachment_ids || comment.attachment_ids.length === 0) {
      return <p className="mt-1 text-gray-700 whitespace-pre-wrap">{comment.text}</p>;
    }
    
    // Simple parsing - just append referenced attachments after the text
    // In a more sophisticated implementation, you might want to parse @[attachment_id] syntax
    return (
      <div>
        <p className="mt-1 text-gray-700 whitespace-pre-wrap">{comment.text}</p>
        {comment.attachment_ids.length > 0 && (
          <div className="mt-2">
            <span className="text-xs text-gray-500">Referenced attachments: </span>
            <div className="flex flex-wrap gap-1 mt-1">
              {comment.attachment_ids.map(id => renderAttachmentReference(id))}
            </div>
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-4 bg-white">
      <div className="flex justify-between items-start">
        <div>
          <span className="font-medium text-gray-900">{comment.author}</span>
          <span className="ml-2 text-xs text-gray-500">{timestampDisplay}</span>
          {comment.is_private && (
            <span className="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded">Private</span>
          )}
        </div>
        {!isEditing && (
          <div className="flex space-x-2">
            <button 
              onClick={() => setIsEditing(true)}
              className="text-gray-500 hover:text-blue-600"
              aria-label="Edit comment"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            <button 
              onClick={handleDelete}
              className="text-gray-500 hover:text-red-600"
              disabled={isDeleting}
              aria-label="Delete comment"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        )}
      </div>
      
      {isEditing ? (
        <div className="mt-2">
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
          />
          {error && <p className="mt-1 text-red-600 text-sm">{error}</p>}
          <div className="mt-2 flex justify-end space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsEditing(false);
                setEditText(comment.text);
                setError(null);
              }}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpdate}
              isLoading={isSaving}
            >
              Save
            </Button>
          </div>
        </div>
      ) : (
        renderCommentText()
      )}
    </div>
  );
};
