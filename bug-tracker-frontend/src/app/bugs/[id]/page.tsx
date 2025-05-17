'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useBugById } from '../../../hooks/useBugs';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { TextArea } from '../../../components/ui/TextArea';
import { Select } from '../../../components/ui/Select';
import { FileUpload } from '../../../components/ui/FileUpload';
import { AttachmentItem } from '../../../components/attachments/AttachmentItem';
import { CommentSection } from '../../../components/comments/CommentSection';
import { 
  BaseSeverity, BaseStatus, Bug, BugSchemaType, 
  MozillaSeverity, MozillaPriority, MozillaStatus, MozillaResolution, 
  ChromiumPriority, ChromiumType, ChromiumStatus,
  BaseTypeCreateRequest, MozillaCreateRequest, ChromiumCreateRequest, OracleCreateRequest 
} from '../../../types/bug';
import { bugAPI, attachmentAPI } from '../../../services/api-client';
import { UpdateBugRequest } from '../../../types/bug';

// Base severity options
const baseSeverityOptions = [
  { value: BaseSeverity.LOW, label: 'Low' },
  { value: BaseSeverity.MEDIUM, label: 'Medium' },
  { value: BaseSeverity.HIGH, label: 'High' },
  { value: BaseSeverity.CRITICAL, label: 'Critical' },
];

// Base status options
const baseStatusOptions = [
  { value: BaseStatus.NEW, label: 'New' },
  { value: BaseStatus.IN_PROGRESS, label: 'In Progress' },
  { value: BaseStatus.RESOLVED, label: 'Resolved' },
  { value: BaseStatus.CLOSED, label: 'Closed' },
];

// Mozilla severity options
const mozillaSeverityOptions = [
  { value: MozillaSeverity.BLOCKER, label: 'Blocker' },
  { value: MozillaSeverity.CRITICAL, label: 'Critical' },
  { value: MozillaSeverity.MAJOR, label: 'Major' },
  { value: MozillaSeverity.NORMAL, label: 'Normal' },
  { value: MozillaSeverity.MINOR, label: 'Minor' },
  { value: MozillaSeverity.TRIVIAL, label: 'Trivial' },
  { value: MozillaSeverity.ENHANCEMENT, label: 'Enhancement' },
];

// Mozilla priority options
const mozillaPriorityOptions = [
  { value: MozillaPriority.P1, label: 'P1' },
  { value: MozillaPriority.P2, label: 'P2' },
  { value: MozillaPriority.P3, label: 'P3' },
  { value: MozillaPriority.P4, label: 'P4' },
  { value: MozillaPriority.P5, label: 'P5' },
];

// Mozilla status options
const mozillaStatusOptions = [
  { value: MozillaStatus.UNCONFIRMED, label: 'Unconfirmed' },
  { value: MozillaStatus.NEW, label: 'New' },
  { value: MozillaStatus.ASSIGNED, label: 'Assigned' },
  { value: MozillaStatus.RESOLVED, label: 'Resolved' },
  { value: MozillaStatus.VERIFIED, label: 'Verified' },
  { value: MozillaStatus.REOPENED, label: 'Reopened' },
];

// Mozilla resolution options
const mozillaResolutionOptions = [
  { value: MozillaResolution.FIXED, label: 'Fixed' },
  { value: MozillaResolution.INVALID, label: 'Invalid' },
  { value: MozillaResolution.WONTFIX, label: 'Won\'t Fix' },
  { value: MozillaResolution.DUPLICATE, label: 'Duplicate' },
  { value: MozillaResolution.WORKSFORME, label: 'Works For Me' },
  { value: MozillaResolution.INCOMPLETE, label: 'Incomplete' },
];

// Chromium priority options
const chromiumPriorityOptions = [
  { value: ChromiumPriority.P0, label: 'P0' },
  { value: ChromiumPriority.P1, label: 'P1' },
  { value: ChromiumPriority.P2, label: 'P2' },
  { value: ChromiumPriority.P3, label: 'P3' },
  { value: ChromiumPriority.P4, label: 'P4' },
];

// Chromium type options
const chromiumTypeOptions = [
  { value: ChromiumType.BUG, label: 'Bug' },
  { value: ChromiumType.FEATURE, label: 'Feature' },
  { value: ChromiumType.FEATURE_REQUEST, label: 'Feature Request' },
  { value: ChromiumType.TASK, label: 'Task' },
];

// Chromium status options
const chromiumStatusOptions = [
  { value: ChromiumStatus.UNCONFIRMED, label: 'Unconfirmed' },
  { value: ChromiumStatus.UNTRIAGED, label: 'Untriaged' },
  { value: ChromiumStatus.ASSIGNED, label: 'Assigned' },
  { value: ChromiumStatus.STARTED, label: 'Started' },
  { value: ChromiumStatus.FIXED, label: 'Fixed' },
  { value: ChromiumStatus.VERIFIED, label: 'Verified' },
  { value: ChromiumStatus.DUPLICATE, label: 'Duplicate' },
  { value: ChromiumStatus.WONTFIX, label: 'Won\'t Fix' },
  { value: ChromiumStatus.ARCHIVED, label: 'Archived' },
];

// Oracle status options - converting numbers to strings for the Select component
const oracleStatusOptions = [
  { value: '10', label: '10 - Description Phase' },
  { value: '11', label: '11 - Code/Hardware Bug' },
  { value: '16', label: '16 - Bug Screening/Triage' },
  { value: '17', label: '17 - Work in Progress' },
  { value: '20', label: '20 - More Info Needed' },
  { value: '30', label: '30 - Waiting for Document' },
  { value: '80', label: '80 - Closed, Fixed' },
  { value: '82', label: '82 - Closed, Cannot Reproduce' },
  { value: '84', label: '84 - Closed, Not Feasible' },
  { value: '90', label: '90 - Closed, Verified by Filer' },
  { value: '92', label: '92 - Closed, Not a Bug' },
  { value: '96', label: '96 - Closed, Duplicate Bug' },
];

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
  const [editMode, setEditMode] = useState<'title' | 'description' | 'fields' | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  
  // Schema-specific field state variables (for Base type)
  const [editBaseSeverity, setEditBaseSeverity] = useState<BaseSeverity | "">("");
  const [editBaseStatus, setEditBaseStatus] = useState<BaseStatus | "">("");
  
  // Mozilla-specific field state variables
  const [editMozillaSeverity, setEditMozillaSeverity] = useState<MozillaSeverity | "">("");
  const [editMozillaPriority, setEditMozillaPriority] = useState<MozillaPriority | "">("");
  const [editMozillaStatus, setEditMozillaStatus] = useState<MozillaStatus | "">("");
  const [editMozillaResolution, setEditMozillaResolution] = useState<MozillaResolution | "">("");
  const [editMozillaVersion, setEditMozillaVersion] = useState('');
  const [editMozillaComponent, setEditMozillaComponent] = useState('');
  const [editMozillaKeywords, setEditMozillaKeywords] = useState('');
  
  // Chromium-specific field state variables
  const [editChromiumPriority, setEditChromiumPriority] = useState<ChromiumPriority | "">("");
  const [editChromiumType, setEditChromiumType] = useState<ChromiumType | "">("");
  const [editChromiumStatus, setEditChromiumStatus] = useState<ChromiumStatus | "">("");
  const [editChromiumComponent, setEditChromiumComponent] = useState('');
  const [editChromiumOwner, setEditChromiumOwner] = useState('');
  const [editChromiumCc, setEditChromiumCc] = useState('');
  const [editChromiumLabels, setEditChromiumLabels] = useState('');
  
  // Oracle-specific field state variables
  const [editOracleStatusCode, setEditOracleStatusCode] = useState<string>('');
  const [editOracleStatusDescription, setEditOracleStatusDescription] = useState('');
  const [editOracleSeverity, setEditOracleSeverity] = useState('');
  const [editOraclePriority, setEditOraclePriority] = useState('');
  const [editOracleCloseReason, setEditOracleCloseReason] = useState('');
  const [editOracleEnvironment, setEditOracleEnvironment] = useState('');
  
  // Function to get the severity value based on bug schema type
  const getBugSeverity = (bug: Bug | null): string | null => {
    if (!bug) return null;
    
    switch (bug.schema_type) {
      case BugSchemaType.BASE:
        return (bug as any).severity || null;
      case BugSchemaType.MOZILLA:
        return (bug as any).mozilla_severity || null;
      case BugSchemaType.CHROMIUM:
        // Chromium doesn't have a direct severity equivalent
        return (bug as any).chromium_priority || null;
      case BugSchemaType.ORACLE:
        return (bug as any).oracle_severity || null;
      default:
        return null;
    }
  };
  
  const getSeverityBadgeColor = (bug: Bug | null) => {
    // Get the appropriate severity based on schema type
    const severity = getBugSeverity(bug);
    
    // Handle case where severity might be undefined
    if (!severity) return 'bg-gray-100 text-gray-800';
    
    // Convert to lowercase to match the BaseSeverity enum values
    const normalizedSeverity = typeof severity === 'string' ? severity.toLowerCase() : '';
    
    // Compare with string values instead of enum values directly
    switch (normalizedSeverity) {
      case 'low':
      case 'p4': // Map Chromium P4 to LOW
      case 'minor': // Map Mozilla minor to LOW
      case 'trivial': // Map Mozilla trivial to LOW
        return 'bg-blue-100 text-blue-800';
        
      case 'medium':
      case 'p3': // Map Chromium P3 to MEDIUM
      case 'normal': // Map Mozilla normal to MEDIUM
        return 'bg-yellow-100 text-yellow-800';
        
      case 'high':
      case 'p2': // Map Chromium P2 to HIGH
      case 'p1': // Map Chromium P1 to HIGH
      case 'major': // Map Mozilla major to HIGH
        return 'bg-orange-100 text-orange-800';
        
      case 'critical':
      case 'p0': // Map Chromium P0 to CRITICAL
      case 'blocker': // Map Mozilla blocker to CRITICAL
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
  
  // Start editing a field (deprecated - using the specific methods below instead)
  const startEditing = (field: 'title' | 'description') => {
    if (!bug) return;
    
    if (field === 'title') {
      startEditTitle();
    } else if (field === 'description') {
      startEditDescription();
    }
  };
  
  const startEditTitle = () => {
    setEditMode('title');
    // Ensure bug title is never undefined before setting state
    setEditTitle(bug?.title || '');
  };
  
  const startEditDescription = () => {
    setEditMode('description');
    // Ensure description is never undefined before setting state
    setEditDescription(bug?.description || '');
  };
  
  // Initialize and start editing schema-specific fields
  const startEditFields = () => {
    if (!bug) return;
    
    setEditMode('fields');
    setSaveError(null);
    
    // Initialize fields based on schema type
    switch (bug.schema_type) {
      case BugSchemaType.BASE:
        // Type cast to access the schema-specific fields
        const baseBug = bug as any;
        setEditBaseSeverity(baseBug.severity || "");
        setEditBaseStatus(baseBug.status || "");
        break;
        
      case BugSchemaType.MOZILLA:
        // Type cast to access the schema-specific fields
        const mozillaBug = bug as any;
        setEditMozillaSeverity(mozillaBug.mozilla_severity || "");
        setEditMozillaPriority(mozillaBug.mozilla_priority || "");
        setEditMozillaStatus(mozillaBug.mozilla_status || "");
        setEditMozillaResolution(mozillaBug.mozilla_resolution || "");
        setEditMozillaVersion(mozillaBug.mozilla_version || "");
        setEditMozillaComponent(mozillaBug.mozilla_component || "");
        setEditMozillaKeywords(mozillaBug.mozilla_keywords || "");
        break;
        
      case BugSchemaType.CHROMIUM:
        // Type cast to access the schema-specific fields
        const chromiumBug = bug as any;
        setEditChromiumPriority(chromiumBug.chromium_priority || "");
        setEditChromiumType(chromiumBug.chromium_type || "");
        setEditChromiumStatus(chromiumBug.chromium_status || "");
        setEditChromiumComponent(chromiumBug.chromium_component || "");
        setEditChromiumOwner(chromiumBug.chromium_owner || "");
        setEditChromiumCc(chromiumBug.chromium_cc || "");
        setEditChromiumLabels(chromiumBug.chromium_labels || "");
        break;
        
      case BugSchemaType.ORACLE:
        // Type cast to access the schema-specific fields
        const oracleBug = bug as any;
        setEditOracleStatusCode(oracleBug.oracle_status_code?.toString() || "");
        setEditOracleStatusDescription(oracleBug.oracle_status_description || "");
        setEditOracleSeverity(oracleBug.oracle_severity || "");
        setEditOraclePriority(oracleBug.oracle_priority || "");
        setEditOracleCloseReason(oracleBug.oracle_close_reason || "");
        setEditOracleEnvironment(oracleBug.oracle_environment || "");
        break;
    }
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
      
      let updateData: any = {};
      
      if (editMode === 'title') {
        if (!editTitle.trim()) {
          setSaveError('Title cannot be empty');
          setIsSaving(false);
          return;
        }
        updateData.title = editTitle.trim();
      } else if (editMode === 'description') {
        updateData.description = editDescription.trim();
      } else if (editMode === 'fields') {
        // Make sure schema_type is set in the update data
        updateData.schema_type = bug.schema_type;
        
        // Add schema-specific fields to the update data
        switch (bug.schema_type) {
          case BugSchemaType.BASE:
            // Create a properly typed object for base bug updates
            if (editBaseSeverity) updateData.severity = editBaseSeverity;
            if (editBaseStatus) updateData.status = editBaseStatus;
            break;
            
          case BugSchemaType.MOZILLA:
            // Create a properly typed object for Mozilla bug updates
            if (editMozillaSeverity) updateData.mozilla_severity = editMozillaSeverity;
            if (editMozillaPriority) updateData.mozilla_priority = editMozillaPriority;
            if (editMozillaStatus) updateData.mozilla_status = editMozillaStatus;
            if (editMozillaResolution) updateData.mozilla_resolution = editMozillaResolution;
            if (editMozillaVersion) updateData.mozilla_version = editMozillaVersion;
            if (editMozillaComponent) updateData.mozilla_component = editMozillaComponent;
            if (editMozillaKeywords) updateData.mozilla_keywords = editMozillaKeywords;
            break;
            
          case BugSchemaType.CHROMIUM:
            // Create a properly typed object for Chromium bug updates
            if (editChromiumPriority) updateData.chromium_priority = editChromiumPriority;
            if (editChromiumType) updateData.chromium_type = editChromiumType;
            if (editChromiumStatus) updateData.chromium_status = editChromiumStatus;
            if (editChromiumComponent) updateData.chromium_component = editChromiumComponent;
            if (editChromiumOwner) updateData.chromium_owner = editChromiumOwner;
            if (editChromiumCc) updateData.chromium_cc = editChromiumCc;
            if (editChromiumLabels) updateData.chromium_labels = editChromiumLabels;
            break;
            
          case BugSchemaType.ORACLE:
            // Create a properly typed object for Oracle bug updates
            if (editOracleStatusCode) updateData.oracle_status_code = parseInt(editOracleStatusCode);
            if (editOracleStatusDescription) updateData.oracle_status_description = editOracleStatusDescription;
            if (editOracleSeverity) updateData.oracle_severity = editOracleSeverity;
            if (editOraclePriority) updateData.oracle_priority = editOraclePriority;
            if (editOracleCloseReason) updateData.oracle_close_reason = editOracleCloseReason;
            if (editOracleEnvironment) updateData.oracle_environment = editOracleEnvironment;
            break;
        }
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
                onClick={() => startEditTitle()} 
                className="ml-2 text-gray-500 hover:text-blue-500 p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Edit title"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500 hover:text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            </div>
          )}
          <div className="flex items-center mt-1 space-x-3">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadgeColor(bug)}`}>
              {getBugSeverity(bug) 
                ? getBugSeverity(bug)!.charAt(0).toUpperCase() + getBugSeverity(bug)!.slice(1).toLowerCase() 
                : 'Unknown'}
            </span>
            <span className="text-sm text-gray-500">
              Reported by {bug.reporter || 'Anonymous'} on {new Date(bug.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Description section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-lg font-medium">Description</h2>
          <button 
            onClick={() => startEditDescription()}
            className="text-gray-500 hover:text-blue-500 p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Edit description"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
        
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
          <div className="prose prose-sm max-w-none">
            {bug.description ? (
              <p className="whitespace-pre-wrap">{bug.description}</p>
            ) : (
              <p className="text-gray-500 italic">No description provided.</p>
            )}
          </div>
        )}
      </div>

      {/* Schema-specific properties section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-lg font-medium">
            {bug.schema_type === BugSchemaType.BASE && 'Bug Properties'}
            {bug.schema_type === BugSchemaType.MOZILLA && 'Mozilla Properties'}
            {bug.schema_type === BugSchemaType.CHROMIUM && 'Chromium Properties'}
            {bug.schema_type === BugSchemaType.ORACLE && 'Oracle Properties'}
          </h2>
          <div>
            <p className="text-sm text-gray-500 mb-1">Schema Type: <span className="font-medium">{bug.schema_type}</span></p>
            {editMode === 'fields' ? (
              <div className="space-y-4 mt-4">
                {/* Render form fields based on bug schema type */}
                {bug.schema_type === BugSchemaType.BASE && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                      <Select 
                        options={baseSeverityOptions}
                        value={editBaseSeverity}
                        onChange={(value) => setEditBaseSeverity(value as BaseSeverity)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <Select 
                        options={baseStatusOptions}
                        value={editBaseStatus}
                        onChange={(value) => setEditBaseStatus(value as BaseStatus)}
                      />
                    </div>
                  </div>
                )}
                
                {bug.schema_type === BugSchemaType.MOZILLA && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                      <Select 
                        options={mozillaSeverityOptions}
                        value={editMozillaSeverity}
                        onChange={(value) => setEditMozillaSeverity(value as MozillaSeverity)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                      <Select 
                        options={mozillaPriorityOptions}
                        value={editMozillaPriority}
                        onChange={(value) => setEditMozillaPriority(value as MozillaPriority)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <Select 
                        options={mozillaStatusOptions}
                        value={editMozillaStatus}
                        onChange={(value) => setEditMozillaStatus(value as MozillaStatus)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Resolution</label>
                      <Select 
                        options={mozillaResolutionOptions}
                        value={editMozillaResolution}
                        onChange={(value) => setEditMozillaResolution(value as MozillaResolution)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Component</label>
                      <Input 
                        value={editMozillaComponent}
                        onChange={(e) => setEditMozillaComponent(e.target.value)}
                        placeholder="Component"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
                      <Input 
                        value={editMozillaVersion}
                        onChange={(e) => setEditMozillaVersion(e.target.value)}
                        placeholder="Version"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Keywords</label>
                      <Input 
                        value={editMozillaKeywords}
                        onChange={(e) => setEditMozillaKeywords(e.target.value)}
                        placeholder="Keywords (comma separated)"
                      />
                    </div>
                  </div>
                )}
                
                {bug.schema_type === BugSchemaType.CHROMIUM && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                      <Select 
                        options={chromiumPriorityOptions}
                        value={editChromiumPriority}
                        onChange={(value) => setEditChromiumPriority(value as ChromiumPriority)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                      <Select 
                        options={chromiumTypeOptions}
                        value={editChromiumType}
                        onChange={(value) => setEditChromiumType(value as ChromiumType)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <Select 
                        options={chromiumStatusOptions}
                        value={editChromiumStatus}
                        onChange={(value) => setEditChromiumStatus(value as ChromiumStatus)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Component</label>
                      <Input 
                        value={editChromiumComponent}
                        onChange={(e) => setEditChromiumComponent(e.target.value)}
                        placeholder="Component"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Owner</label>
                      <Input 
                        value={editChromiumOwner}
                        onChange={(e) => setEditChromiumOwner(e.target.value)}
                        placeholder="Owner"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">CC</label>
                      <Input 
                        value={editChromiumCc}
                        onChange={(e) => setEditChromiumCc(e.target.value)}
                        placeholder="CC (email addresses)"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Labels</label>
                      <Input 
                        value={editChromiumLabels}
                        onChange={(e) => setEditChromiumLabels(e.target.value)}
                        placeholder="Labels (comma separated)"
                      />
                    </div>
                  </div>
                )}
                
                {bug.schema_type === BugSchemaType.ORACLE && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status Code</label>
                      <Select 
                        options={oracleStatusOptions}
                        value={editOracleStatusCode}
                        onChange={(value) => setEditOracleStatusCode(value as string)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status Description</label>
                      <Input 
                        value={editOracleStatusDescription}
                        onChange={(e) => setEditOracleStatusDescription(e.target.value)}
                        placeholder="Status description"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                      <Input 
                        value={editOracleSeverity}
                        onChange={(e) => setEditOracleSeverity(e.target.value)}
                        placeholder="Severity"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                      <Input 
                        value={editOraclePriority}
                        onChange={(e) => setEditOraclePriority(e.target.value)}
                        placeholder="Priority"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Close Reason</label>
                      <Input 
                        value={editOracleCloseReason}
                        onChange={(e) => setEditOracleCloseReason(e.target.value)}
                        placeholder="Close reason"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                      <TextArea 
                        value={editOracleEnvironment}
                        onChange={(e) => setEditOracleEnvironment(e.target.value)}
                        placeholder="Environment details"
                        rows={3}
                      />
                    </div>
                  </div>
                )}
                
                {/* Action buttons */}
                <div className="flex justify-end space-x-2 pt-4">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={saveField}
                    isLoading={isSaving}
                  >
                    Save Changes
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
              <div className="mt-4">
                {/* Display schema-specific field values in read-only mode */}
                {bug.schema_type === BugSchemaType.BASE && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Severity</p>
                      <p className="text-sm text-gray-900">{(bug as any).severity || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Status</p>
                      <p className="text-sm text-gray-900">{(bug as any).status || 'Not set'}</p>
                    </div>
                  </div>
                )}
                
                {bug.schema_type === BugSchemaType.MOZILLA && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Severity</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_severity || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Priority</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_priority || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Status</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_status || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Resolution</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_resolution || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Component</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_component || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Version</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_version || 'Not set'}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-700">Keywords</p>
                      <p className="text-sm text-gray-900">{(bug as any).mozilla_keywords || 'Not set'}</p>
                    </div>
                  </div>
                )}
                
                {bug.schema_type === BugSchemaType.CHROMIUM && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Priority</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_priority || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Type</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_type || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Status</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_status || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Component</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_component || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Owner</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_owner || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">CC</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_cc || 'Not set'}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-700">Labels</p>
                      <p className="text-sm text-gray-900">{(bug as any).chromium_labels || 'Not set'}</p>
                    </div>
                  </div>
                )}
                
                {bug.schema_type === BugSchemaType.ORACLE && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Status Code</p>
                      <p className="text-sm text-gray-900">{(bug as any).oracle_status_code || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Status Description</p>
                      <p className="text-sm text-gray-900">{(bug as any).oracle_status_description || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Severity</p>
                      <p className="text-sm text-gray-900">{(bug as any).oracle_severity || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Priority</p>
                      <p className="text-sm text-gray-900">{(bug as any).oracle_priority || 'Not set'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Close Reason</p>
                      <p className="text-sm text-gray-900">{(bug as any).oracle_close_reason || 'Not set'}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-700">Environment</p>
                      <p className="text-sm text-gray-900 whitespace-pre-wrap">{(bug as any).oracle_environment || 'Not set'}</p>
                    </div>
                  </div>
                )}
                
                <div className="mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={startEditFields}
                  >
                    Edit Properties
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
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
