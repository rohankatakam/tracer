'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useBugById } from '../../../hooks/useBugs';
import { Button } from '../../../components/ui/Button';
import { FileUpload } from '../../../components/ui/FileUpload';
import { AttachmentItem } from '../../../components/attachments/AttachmentItem';
import { CommentSection } from '../../../components/comments/CommentSection';
import { SeverityLevel } from '../../../types/bug';
import { bugAPI, attachmentAPI } from '../../../services/api-client';
import { UpdateBugRequest } from '../../../types/bug';

interface BugDetailPageProps {
  params: {
    id: string;
  };
}

export default function BugDetailPage({ params }: BugDetailPageProps) {
  const router = useRouter();
  
  // Normalize the bug ID to ensure consistent formatting
  const bugId = params.id;
  
  // Log the ID from the URL for debugging
  console.log(`Bug ID from URL: ${bugId}`);
  
  const { bug, isLoading, error } = useBugById(bugId);
  
  const refreshBug = () => window.location.reload();
  
  // Original state variables
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showAttachmentContent, setShowAttachmentContent] = useState<string | null>(null);
  const [attachmentContent, setAttachmentContent] = useState<any>(null);
  const [contentLoading, setContentLoading] = useState(false);
  
  // Edit mode state variables
  const [editMode, setEditMode] = useState<'title' | 'description' | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  
  const getSeverityBadgeColor = (severity: SeverityLevel) => {
    switch (severity) {
      case SeverityLevel.LOW:
        return 'bg-blue-100 text-blue-800';
      case SeverityLevel.MEDIUM:
        return 'bg-yellow-100 text-yellow-800';
      case SeverityLevel.HIGH:
        return 'bg-orange-100 text-orange-800';
      case SeverityLevel.CRITICAL:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this bug? This action cannot be undone.')) {
      try {
        setIsDeleting(true);
        await bugAPI.delete(bugId);
        router.push('/bugs');
      } catch (error) {
        console.error('Error deleting bug:', error);
        alert('Failed to delete bug. Please try again.');
        setIsDeleting(false);
      }
    }
  };

  const handleFileUpload = async (files: File[]) => {
    if (files.length === 0 || !bug) return;
    
    try {
      setIsUploading(true);
      setUploadError(null);
      
      for (const file of files) {
        await attachmentAPI.uploadAttachment(bug.bug_id, file);
      }
      
      // Refresh bug data to show new attachments
      window.location.reload();
    } catch (error) {
      console.error('Error uploading attachment:', error);
      setUploadError('Failed to upload attachment. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleViewAttachmentContent = async (attachmentId: string) => {
    try {
      setContentLoading(true);
      setShowAttachmentContent(attachmentId);
      const content = await attachmentAPI.getAttachmentContent(attachmentId);
      setAttachmentContent(content);
    } catch (error) {
      console.error('Error fetching attachment content:', error);
      // More detailed error message
      setAttachmentContent({ 
        error: 'Failed to load content. The server returned an error (500 Internal Server Error). '
        + 'This is likely due to the attachment processing not being fully implemented on the backend. '
        + 'You may need to update the server-side code to handle this attachment type.'
      });
    } finally {
      setContentLoading(false);
    }
  };
  
  // Start editing a field
  const startEditing = (field: 'title' | 'description') => {
    if (!bug) return;
    
    if (field === 'title') {
      setEditTitle(bug.title);
    } else if (field === 'description') {
      setEditDescription(bug.description);
    }
    
    setEditMode(field);
    setSaveError(null);
  };
  
  // Cancel editing
  const cancelEditing = () => {
    setEditMode(null);
    setSaveError(null);
  };
  
  // Save edited field
  const saveField = async () => {
    if (!bug || !editMode) return;
    
    try {
      setIsSaving(true);
      setSaveError(null);
      
      const updateData: UpdateBugRequest = {};
      
      if (editMode === 'title') {
        if (!editTitle.trim()) {
          setSaveError('Title cannot be empty');
          setIsSaving(false);
          return;
        }
        updateData.title = editTitle.trim();
      } else if (editMode === 'description') {
        updateData.description = editDescription.trim();
      }
      
      await bugAPI.update(bug.bug_id, updateData);
      
      // Refresh the bug data
      await refreshBug();
      
      // Exit edit mode
      setEditMode(null);
    } catch (error) {
      console.error('Error updating bug:', error);
      setSaveError('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-10">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="mt-2 text-gray-500">Loading bug details...</p>
      </div>
    );
  }

  if (error || !bug) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <p>{error || 'Bug not found'}</p>
        <button 
          onClick={() => router.push('/bugs')}
          className="underline text-red-700 mt-2"
        >
          Back to Bugs
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-start mb-6">
        <div>
          {editMode === 'title' ? (
            <div className="space-y-2">
              <textarea
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-2xl font-bold"
                rows={2}
                placeholder="Bug title"
                autoFocus
              />
              {saveError && (
                <div className="text-sm text-red-600">{saveError}</div>
              )}
              <div className="flex space-x-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={saveField}
                  isLoading={isSaving}
                >
                  Save
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={cancelEditing}
                  disabled={isSaving}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="group relative">
              <h1 className="text-2xl font-bold text-gray-900">{bug.title}</h1>
              <button
                onClick={() => startEditing('title')}
                className="absolute -right-8 top-1 opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label="Edit title"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500 hover:text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            </div>
          )}
          <div className="flex items-center mt-1 space-x-3">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadgeColor(bug.severity)}`}>
              {bug.severity.charAt(0).toUpperCase() + bug.severity.slice(1)}
            </span>
            <span className="text-sm text-gray-500">
              Reported by {bug.reporter || 'Anonymous'} on {new Date(bug.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={() => router.push('/bugs')}
          >
            Back to Bugs
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            isLoading={isDeleting}
          >
            Delete Bug
          </Button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium mb-3">Description</h2>
        {editMode === 'description' ? (
          <div className="space-y-2">
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[150px]"
              placeholder="Bug description"
              autoFocus
            />
            {saveError && (
              <div className="text-sm text-red-600">{saveError}</div>
            )}
            <div className="flex space-x-2">
              <Button
                variant="primary"
                size="sm"
                onClick={saveField}
                isLoading={isSaving}
              >
                Save
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={cancelEditing}
                disabled={isSaving}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="group relative">
            <p className="whitespace-pre-wrap text-gray-700">{bug.description || <span className="text-gray-400 italic">No description provided</span>}</p>
            <button
              onClick={() => startEditing('description')}
              className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity"
              aria-label="Edit description"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500 hover:text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
          </div>
        )}
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium mb-3">Attachments</h2>
        
        {bug.attachments && bug.attachments.length > 0 ? (
          <div className="space-y-3">
            {bug.attachments.map((attachment) => (
              <AttachmentItem
                key={attachment.attachment_id}
                attachment={attachment}
                onViewContent={() => handleViewAttachmentContent(attachment.attachment_id)}
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No attachments for this bug yet.</p>
        )}

        <div className="mt-6 border-t pt-4">
          <h3 className="text-md font-medium mb-3">Add New Attachment</h3>
          <FileUpload
            accept=".jpg,.jpeg,.png,.pdf,.txt"
            onChange={handleFileUpload}
            error={uploadError || undefined}
          />
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium mb-3">Comments</h2>
        {bug && (
          <CommentSection 
            bugId={bug.bug_id} 
            attachments={bug.attachments || []}
          />
        )}
      </div>

      {/* Attachment Content Modal */}
      {showAttachmentContent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-auto">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-medium">Attachment Content</h3>
              <button
                onClick={() => {
                  setShowAttachmentContent(null);
                  setAttachmentContent(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6">
              {contentLoading ? (
                <div className="text-center py-10">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <p className="mt-2 text-gray-500">Loading content...</p>
                </div>
              ) : attachmentContent ? (
                <>
                  {attachmentContent.error ? (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                      {attachmentContent.error}
                    </div>
                  ) : attachmentContent.content_type?.startsWith('image/') ? (
                    <div className="flex justify-center">
                      <img
                        src={`data:${attachmentContent.content_type};base64,${attachmentContent.base64_content}`}
                        alt="Attachment content"
                        className="max-w-full max-h-[70vh] object-contain"
                      />
                    </div>
                  ) : attachmentContent.text_content ? (
                    <div className="bg-gray-50 p-4 rounded max-h-[70vh] overflow-y-auto">
                      <pre className="whitespace-pre-wrap font-mono text-sm">
                        {attachmentContent.text_content}
                      </pre>
                    </div>
                  ) : attachmentContent.content_type === 'application/pdf' && attachmentContent.base64_content ? (
                    <div className="flex flex-col items-center">
                      <div className="mb-4">
                        <h3 className="text-lg font-medium">PDF Document: {attachmentContent.filename}</h3>
                        <p className="text-sm text-gray-500">Size: {(attachmentContent.file_size / 1024).toFixed(1)} KB</p>
                      </div>
                      <iframe
                        src={`data:application/pdf;base64,${attachmentContent.base64_content}`}
                        width="100%"
                        height="600px"
                        style={{ border: '1px solid #e5e7eb', borderRadius: '0.375rem' }}
                        title="PDF Document"
                      />
                    </div>
                  ) : attachmentContent.pages ? (
                    <div className="bg-gray-50 p-4 rounded max-h-[70vh] overflow-y-auto">
                      <h3 className="text-lg font-medium mb-4">PDF Content</h3>
                      {attachmentContent.pages.map((page: any, index: number) => (
                        <div key={index} className="mb-4 pb-4 border-b border-gray-200">
                          <h4 className="font-medium mb-2">Page {page.page_number}</h4>
                          <p className="whitespace-pre-wrap">{page.text}</p>
                        </div>
                      ))}
                    </div>
                  ) : attachmentContent.message ? (
                    <div className="text-center text-gray-500 p-4">
                      <p className="mb-2 font-medium">{attachmentContent.message}</p>
                      <p>File: {attachmentContent.filename}</p>
                      <p>Size: {(attachmentContent.file_size / 1024).toFixed(1)} KB</p>
                      <p>Type: {attachmentContent.content_type}</p>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500">
                      This content type cannot be previewed directly.
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center text-gray-500">
                  No content available.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
