'use client';

import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { commentAPI } from '../../services/api-client';
import { Attachment } from '../../types/bug';

interface CommentFormProps {
  bugId: string;
  attachments?: Attachment[];
  onCommentAdded: () => void;
}

export const CommentForm: React.FC<CommentFormProps> = ({ 
  bugId, 
  attachments = [], 
  onCommentAdded 
}) => {
  const [text, setText] = useState('');
  const [author, setAuthor] = useState('');
  const [selectedAttachments, setSelectedAttachments] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAttachmentSelector, setShowAttachmentSelector] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Comment text is required');
      return;
    }
    
    if (!author.trim()) {
      setError('Author name is required');
      return;
    }
    
    try {
      setIsSubmitting(true);
      setError(null);
      
      await commentAPI.createComment(bugId, {
        text: text.trim(),
        author: author.trim(),
        attachment_ids: selectedAttachments.length > 0 ? selectedAttachments : undefined
      });
      
      // Reset form
      setText('');
      setSelectedAttachments([]);
      setShowAttachmentSelector(false);
      
      // Notify parent
      onCommentAdded();
    } catch (err) {
      console.error('Error adding comment:', err);
      setError('Failed to add comment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const toggleAttachmentSelection = (attachmentId: string) => {
    setSelectedAttachments(prev => 
      prev.includes(attachmentId)
        ? prev.filter(id => id !== attachmentId)
        : [...prev, attachmentId]
    );
  };
  
  const handleAttachmentReference = () => {
    setShowAttachmentSelector(!showAttachmentSelector);
  };
  
  // Function to insert attachment reference into text (optional enhancement)
  const insertAttachmentReference = (attachmentId: string) => {
    const reference = `@[${attachmentId}]`;
    setText(prevText => prevText + reference + ' ');
    toggleAttachmentSelection(attachmentId);
  };
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <h3 className="text-lg font-medium mb-3">Add Comment</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Your name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        
        <div className="mb-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Add your comment here..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
            required
          ></textarea>
        </div>
        
        {/* Attachment reference button and selector */}
        {attachments.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center mb-2">
              <button
                type="button"
                onClick={handleAttachmentReference}
                className="flex items-center text-sm text-blue-600 hover:text-blue-800"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                {showAttachmentSelector ? 'Hide attachments' : 'Reference attachments'}
              </button>
              
              {selectedAttachments.length > 0 && (
                <span className="ml-2 text-xs text-gray-500">
                  {selectedAttachments.length} attachment(s) selected
                </span>
              )}
            </div>
            
            {showAttachmentSelector && (
              <div className="bg-gray-50 p-3 rounded-md mb-3">
                <div className="text-sm font-medium mb-2">Select attachments to reference:</div>
                <div className="flex flex-wrap gap-2">
                  {attachments.map(attachment => (
                    <div 
                      key={attachment.attachment_id}
                      className={`
                        cursor-pointer p-2 rounded border
                        ${selectedAttachments.includes(attachment.attachment_id) 
                          ? 'bg-blue-50 border-blue-300' 
                          : 'bg-white border-gray-200 hover:bg-gray-50'}
                      `}
                      onClick={() => toggleAttachmentSelection(attachment.attachment_id)}
                    >
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedAttachments.includes(attachment.attachment_id)}
                          onChange={() => toggleAttachmentSelection(attachment.attachment_id)}
                          className="mr-2"
                        />
                        <span className="text-sm">{attachment.filename}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {error && (
          <div className="mb-3 p-2 bg-red-50 text-red-600 text-sm rounded">
            {error}
          </div>
        )}
        
        <div className="flex justify-end">
          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            disabled={isSubmitting}
          >
            Add Comment
          </Button>
        </div>
      </form>
    </div>
  );
};
