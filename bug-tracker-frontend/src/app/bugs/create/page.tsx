'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import Link from 'next/link';
import axios from 'axios';

// Component imports
import { GitHubIssueImportModal } from '../../../components/bugs/GitHubIssueImportModal';
import { Input } from '../../../components/ui/Input';
import { Button } from '../../../components/ui/Button';
import { TextArea } from '../../../components/ui/TextArea';
import { Select } from '../../../components/ui/Select';
import { FileUpload } from '../../../components/ui/FileUpload';

// Service imports
import { attachmentAPI, bugAPI } from '../../../services/api-client';
import { fetchGitHubIssue } from '../../../services/github-api';

// Type imports
import { 
  BaseSeverity, 
  BaseStatus, 
  Bug, 
  BugSchemaType, 
  BaseTypeCreateRequest,
  ChromiumCreateRequest, 
  ChromiumPriority, 
  ChromiumStatus, 
  ChromiumType, 
  CreateBugRequest, 
  GitHubIssueCreateRequest,
  MozillaCreateRequest, 
  MozillaPriority, 
  MozillaResolution,
  MozillaSeverity, 
  MozillaStatus, 
  OracleCreateRequest 
} from '../../../types/bug';

// Bug schema type options
const schemaTypeOptions = [
  { value: BugSchemaType.BASE, label: 'Base' },
  { value: BugSchemaType.MOZILLA, label: 'Mozilla/Bugzilla' },
  { value: BugSchemaType.CHROMIUM, label: 'Chromium Issue' },
  { value: BugSchemaType.ORACLE, label: 'Oracle' },
  { value: BugSchemaType.GITHUB_ISSUE, label: 'GitHub Issue' },
];

// General Bug Schema Type Options
const bugSchemaOptions = [
  { value: BugSchemaType.BASE, label: 'Base Bug' },
  { value: BugSchemaType.MOZILLA, label: 'Mozilla/Bugzilla' },
  { value: BugSchemaType.CHROMIUM, label: 'Chromium' },
  { value: BugSchemaType.ORACLE, label: 'Oracle' },
  { value: BugSchemaType.GITHUB_ISSUE, label: 'GitHub Issue' },
];

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
  { value: '24', label: '24 - Deferred, Awaiting Engineering' },
  { value: '25', label: '25 - Open, Awaiting Review' },
  { value: '31', label: '31 - Could Not Reproduce' },
  { value: '32', label: '32 - Not a Bug' },
  { value: '36', label: '36 - Duplicate Bug' },
  { value: '60', label: '60 - Fix Available Awaiting Promotion' },
  { value: '74', label: '74 - Closed, Fix Verified' },
  { value: '84', label: '84 - Closed, Not Feasible' },
  { value: '90', label: '90 - Closed, Verified by Filer' },
  { value: '92', label: '92 - Closed, Not a Bug' },
  { value: '96', label: '96 - Closed, Duplicate Bug' },
];

export default function CreateBugPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedSchemaType, setSelectedSchemaType] = useState<BugSchemaType>(BugSchemaType.BASE);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoadingGitHubIssue, setIsLoadingGitHubIssue] = useState(false);
  const [githubIssueError, setGithubIssueError] = useState<string | null>(null);
  const [schemaTypeSelected, setSchemaTypeSelected] = useState<boolean>(false);
  // Ref to track if we've already processed a GitHub URL - must be declared at component level
  const hasProcessedUrlRef = React.useRef(false);
  
  // Create default values based on the schema type
  const getDefaultValues = () => {
    const commonDefaults = {
      title: '',
      description: '',
      reporter: '',
      product: '',
      component: '',
      version: '',
      platform: '',
      operating_system: '',
    };

    // Add schema-specific defaults
    switch (selectedSchemaType) {
      case BugSchemaType.BASE:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.BASE,
          severity: BaseSeverity.MEDIUM,
          status: BaseStatus.NEW,
        } as BaseTypeCreateRequest;
      
      case BugSchemaType.MOZILLA:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.MOZILLA,
          mozilla_severity: MozillaSeverity.NORMAL,
          mozilla_priority: MozillaPriority.P3,
          mozilla_status: MozillaStatus.NEW,
        } as MozillaCreateRequest;
      
      case BugSchemaType.CHROMIUM:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.CHROMIUM,
          chromium_priority: ChromiumPriority.P2,
          chromium_type: ChromiumType.BUG,
          chromium_status: ChromiumStatus.UNTRIAGED,
        } as ChromiumCreateRequest;
      
      case BugSchemaType.ORACLE:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.ORACLE,
          oracle_status_code: 10, // Description Phase
          oracle_severity: 'Medium',
        } as OracleCreateRequest;
      
      case BugSchemaType.GITHUB_ISSUE:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.GITHUB_ISSUE,
          github_issue_number: 0,
          github_state: 'open',
          github_labels: [],
          github_assignees: [],
        } as GitHubIssueCreateRequest;

      default:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.BASE,
          severity: BaseSeverity.MEDIUM,
          status: BaseStatus.NEW,
        } as BaseTypeCreateRequest;
    }
  };
  
  // Define a type that includes all possible error fields from all bug schema types
  type BugFormErrors = {
    [key: string]: { message?: string }
  };

  // Initialize form with stricter validation for required fields
  const { 
    control,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors },
  } = useForm<CreateBugRequest>({
    defaultValues: getDefaultValues(),
    mode: 'onBlur', // Validate on blur for better user experience
  });
  
  // Effect to handle GitHub Issue import from URL parameter
  useEffect(() => {
    const githubIssueUrl = searchParams.get('githubIssueUrl');
    
    if (githubIssueUrl && !hasProcessedUrlRef.current) {
      hasProcessedUrlRef.current = true; // Mark as processed for this URL
      
      const loadGitHubIssue = async () => {
        try {
          setIsLoadingGitHubIssue(true);
          setGithubIssueError(null);
          
          // Set schema type state
          setSelectedSchemaType(BugSchemaType.GITHUB_ISSUE);
          setSchemaTypeSelected(true);

          // Prepare a complete default object for resetting to GitHub issue type
          // This ensures all fields are initialized correctly according to GitHubIssueCreateRequest
          const defaultsForGithubReset: GitHubIssueCreateRequest = {
            title: '',
            description: '',
            reporter: '', // Will be overwritten by setValue from issueData.user.login if available
            product: '',
            component: '',
            version: '',
            platform: '',
            operating_system: '',
            schema_type: BugSchemaType.GITHUB_ISSUE,
            github_issue_number: 0,
            github_state: 'open',
            github_labels: [],
            github_assignees: [],
            github_issue_url: '',
            github_repo: '',
            github_owner: '',
            github_created_at: new Date().toISOString(), // Placeholder, will be updated
            github_updated_at: new Date().toISOString(), // Placeholder, will be updated
            github_closed_at: null, // Placeholder, will be updated if issue is closed
            // Include other fields from GitHubIssueCreateRequest initialized to their defaults
          };
          reset(defaultsForGithubReset);

          // Fetch GitHub issue data with a timeout
          const controller = new AbortController();
          const timeoutId = setTimeout(() => {
            controller.abort();
            console.warn('GitHub issue fetch timed out for URL:', githubIssueUrl);
          }, 10000); // 10-second timeout

          try {
            const issueData = await fetchGitHubIssue(decodeURIComponent(githubIssueUrl));
            clearTimeout(timeoutId); // Clear timeout as fetch was successful
            
            // Populate form with GitHub issue data
            setValue('schema_type', BugSchemaType.GITHUB_ISSUE, { shouldValidate: true });
            setValue('title', issueData.title || 'Untitled Issue', { shouldValidate: true });
            setValue('description', issueData.body || '', { shouldValidate: true });
            setValue('reporter', issueData.user?.login || '', { shouldValidate: true });

            setValue('github_issue_number', typeof issueData.number === 'number' ? issueData.number : 0);
            setValue('github_issue_url', issueData.html_url || '');
            setValue('github_repo', issueData.repository?.name || '');
            setValue('github_owner', issueData.repository?.owner?.login || '');
            setValue('github_state', issueData.state || 'open');
            
            setValue('github_labels', 
              Array.isArray(issueData.labels) 
                ? issueData.labels.map((label: any) => (label && typeof label === 'object' && label.name) || '').filter(Boolean) 
                : []
            );
            setValue('github_assignees', 
              Array.isArray(issueData.assignees) 
                ? issueData.assignees.map((assignee: any) => (assignee && typeof assignee === 'object' && assignee.login) || '').filter(Boolean) 
                : []
            );
            
            setValue('github_created_at', issueData.created_at || new Date().toISOString());
            setValue('github_updated_at', issueData.updated_at || new Date().toISOString());
            if (issueData.closed_at) {
              setValue('github_closed_at', issueData.closed_at);
            } else {
              setValue('github_closed_at', null); // Explicitly set to null if not closed
            }

          } catch (fetchError: any) {
            clearTimeout(timeoutId); // Clear timeout if fetch itself failed
            console.error('Error fetching or processing GitHub issue data:', fetchError);
            const message = fetchError?.message || 'Unknown error';
            if (fetchError?.name === 'AbortError') {
              setGithubIssueError('Failed to load GitHub issue: Request timed out. Check URL/network.');
            } else {
              setGithubIssueError(`Failed to load GitHub issue: ${message}. Check URL and try again.`);
            }
          }
        } catch (outerError: any) {
          console.error('Error in loadGitHubIssue setup:', outerError);
          setGithubIssueError('An unexpected error occurred. Please refresh and try again.');
        } finally {
          setIsLoadingGitHubIssue(false);
        }
      };
      
      loadGitHubIssue();
    }
  }, [searchParams, reset, setValue, setSelectedSchemaType, setSchemaTypeSelected, setIsLoadingGitHubIssue, setGithubIssueError, hasProcessedUrlRef]);
  
  // Cast errors to the more permissive type to avoid TypeScript errors with union types
  const formErrors = errors as BugFormErrors;

  // Watch for schema type changes to update form fields
  const watchedSchemaType = watch('schema_type');
  
  // Handle schema type changes
  const handleSchemaTypeChange = (type: BugSchemaType) => {
    if (!schemaTypeSelected) {
      setSelectedSchemaType(type);
      setSchemaTypeSelected(true);
      // Reset the form with new default values based on the selected schema type
      reset({
        ...getDefaultValues(),
        schema_type: type
      });
    }
  };
  
  useEffect(() => {
    // Only process schema type changes when the type isn't already selected
    // This prevents infinite loops
    if (watchedSchemaType !== selectedSchemaType && !schemaTypeSelected) {
      handleSchemaTypeChange(watchedSchemaType as BugSchemaType);
    }
  }, [watchedSchemaType]);

  const onFilesSelect = (files: File[]) => {
    setSelectedFiles(files);
  };

  const onSubmit = async (data: CreateBugRequest) => {
    try {
      setIsSubmitting(true);
      setSubmitError(null);
      
      // Ensure all required fields are present for GitHub Issues
      if (data.schema_type === BugSchemaType.GITHUB_ISSUE) {
        // Format data for FastAPI compatibility
        // FastAPI is strict about null vs undefined and empty arrays vs empty strings
        const gitHubData = data as GitHubIssueCreateRequest;
        
        // Create a clean object with only the fields the API expects
        const processedData = {
          schema_type: BugSchemaType.GITHUB_ISSUE,
          title: gitHubData.title || 'Untitled Issue',
          description: gitHubData.description || '',
          reporter: gitHubData.reporter || '',
          product: gitHubData.product || '',
          component: gitHubData.component || '',
          version: gitHubData.version || '',
          platform: gitHubData.platform || '',
          operating_system: gitHubData.operating_system || '',
          
          // GitHub specific fields
          github_issue_number: gitHubData.github_issue_number || 0,
          github_issue_url: gitHubData.github_issue_url || '',
          github_repo: gitHubData.github_repo || '',
          github_owner: gitHubData.github_owner || '',
          github_state: gitHubData.github_state || 'open',
          
          // Convert arrays to proper formats for FastAPI
          github_labels: Array.isArray(gitHubData.github_labels) ? gitHubData.github_labels : [],
          github_assignees: Array.isArray(gitHubData.github_assignees) ? gitHubData.github_assignees : [],
          
          // Format dates as proper ISO strings
          github_created_at: gitHubData.github_created_at || new Date().toISOString(),
          github_updated_at: gitHubData.github_updated_at || new Date().toISOString()
        };
        
        console.log('Submitting GitHub issue bug with data:', processedData);
        
        // Step 1: Create the bug with processed data
        const newBug = await bugAPI.create(processedData);
        
        // Steps 2-3 remain the same...
        if (selectedFiles.length > 0) {
          setUploadProgress(0);
          
          for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            await attachmentAPI.uploadAttachment(newBug.bug_id, file);
            setUploadProgress(Math.round(((i + 1) / selectedFiles.length) * 100));
          }
        }
        
        // Navigate to the newly created bug
        router.push(`/bugs/${newBug.bug_id}`);
      } else {
        // For non-GitHub issues, use the original flow
        console.log('Submitting regular bug with data:', data);
        
        // Step 1: Create the bug
        const newBug = await bugAPI.create(data);
        
        // Step 2: Upload attachments (if any)
        if (selectedFiles.length > 0) {
          setUploadProgress(0);
          
          for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            await attachmentAPI.uploadAttachment(newBug.bug_id, file);
            setUploadProgress(Math.round(((i + 1) / selectedFiles.length) * 100));
          }
        }
        
        // Step 3: Navigate to the newly created bug
        router.push(`/bugs/${newBug.bug_id}`);
      }
    } catch (error) {
      console.error('Error creating bug:', error);
      // More detailed error message from the API response
      let errorMessage = 'Failed to create bug. Please try again.';
      
      // Safe type checking for Axios errors
      if (error && typeof error === 'object' && 'isAxiosError' in error) {
        const axiosError = error as any;
        if (axiosError.response?.data) {
          console.log('API error details:', axiosError.response.data);
          if (axiosError.response.status === 422) {
            errorMessage = 'Validation error: Some required fields are missing or invalid. Check the GitHub issue data format.';
            // Log detailed validation errors if available
            if (axiosError.response.data.detail) {
              console.log('Validation errors:', axiosError.response.data.detail);
            }
          } else {
            errorMessage = `Server error: ${axiosError.response.status} - ${JSON.stringify(axiosError.response.data)}`;
          }
        }
      }
      
      setSubmitError(errorMessage);
      setIsSubmitting(false);
    }
  };

  // Rendering helper functions
  const renderCommonFields = () => (
    <>
      <div>
        <Controller
          name="title"
          control={control}
          rules={{ required: 'Title is required' }}
          render={({ field }) => (
            <Input
              {...field}
              label="Title"
              placeholder="Brief summary of the bug"
              error={formErrors.title?.message}
            />
          )}
        />
      </div>
      
      <div>
        <Controller
          name="description"
          control={control}
          rules={{ required: 'Description is required' }}
          render={({ field }) => (
            <TextArea
              {...field}
              label="Description"
              placeholder="Detailed description of the bug, including steps to reproduce and expected behavior"
              rows={6}
              error={formErrors.description?.message}
            />
          )}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="reporter"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Reporter"
                placeholder="Your name (optional)"
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="schema_type"
            control={control}
            rules={{ required: 'Bug schema type is required' }}
            render={({ field }) => (
              <Select
                label="Bug Schema Type"
                options={schemaTypeOptions}
                value={field.value}
                onChange={(value) => {
                  field.onChange(value);
                  if (!schemaTypeSelected) {
                    handleSchemaTypeChange(value as BugSchemaType);
                  }
                }}
                error={formErrors.schema_type?.message}
                disabled={schemaTypeSelected}
                helpText={schemaTypeSelected ? "Schema type cannot be changed after selection" : "Select the bug schema type that best matches this bug"}
              />
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="product"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Product"
                placeholder="Product name"
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="component"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Component"
                placeholder="Component name"
              />
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="version"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Version"
                placeholder="Version number"
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="platform"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Platform"
                placeholder="e.g., Desktop, Mobile, etc."
              />
            )}
          />
        </div>
      </div>

      <div>
        <Controller
          name="operating_system"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              label="Operating System"
              placeholder="e.g., Windows 11, macOS, Linux, etc."
            />
          )}
        />
      </div>
    </>
  );

  // Base schema-specific fields
  const renderBaseFields = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <Controller
          name="severity"
          control={control}
          render={({ field }) => (
            <Select
              label="Severity"
              options={baseSeverityOptions}
              value={field.value}
              onChange={field.onChange}
              error={formErrors.severity?.message}
            />
          )}
        />
      </div>
      
      <div>
        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <Select
              label="Status"
              options={baseStatusOptions}
              value={field.value}
              onChange={field.onChange}
              error={formErrors.status?.message}
            />
          )}
        />
      </div>
    </div>
  );

  // Mozilla/Bugzilla schema-specific fields
  const renderMozillaFields = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="mozilla_severity"
            control={control}
            render={({ field }) => (
              <Select
                label="Mozilla Severity"
                options={mozillaSeverityOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.mozilla_severity?.message}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="mozilla_priority"
            control={control}
            render={({ field }) => (
              <Select
                label="Mozilla Priority"
                options={mozillaPriorityOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.mozilla_priority?.message}
              />
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="mozilla_status"
            control={control}
            render={({ field }) => (
              <Select
                label="Mozilla Status"
                options={mozillaStatusOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.mozilla_status?.message}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="mozilla_resolution"
            control={control}
            render={({ field }) => (
              <Select
                label="Mozilla Resolution"
                options={mozillaResolutionOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.mozilla_resolution?.message}
              />
            )}
          />
        </div>
      </div>

      <div>
        <Controller
          name="mozilla_keywords"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              label="Keywords"
              placeholder="Comma-separated keywords"
            />
          )}
        />
      </div>
    </>
  );

  // Chromium schema-specific fields
  const renderChromiumFields = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="chromium_priority"
            control={control}
            render={({ field }) => (
              <Select
                label="Chromium Priority"
                options={chromiumPriorityOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.chromium_priority?.message}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="chromium_type"
            control={control}
            render={({ field }) => (
              <Select
                label="Chromium Type"
                options={chromiumTypeOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.chromium_type?.message}
              />
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="chromium_status"
            control={control}
            render={({ field }) => (
              <Select
                label="Chromium Status"
                options={chromiumStatusOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.chromium_status?.message}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="chromium_owner"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Owner"
                placeholder="Email address of the owner"
              />
            )}
          />
        </div>
      </div>

      <div>
        <Controller
          name="chromium_cc"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              label="CC List"
              placeholder="Comma-separated email addresses"
            />
          )}
        />
      </div>

      <div>
        <Controller
          name="chromium_labels"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              label="Labels"
              placeholder="Comma-separated labels"
            />
          )}
        />
      </div>
    </>
  );

  // Oracle schema-specific fields
  const renderOracleFields = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="oracle_status_code"
            control={control}
            render={({ field }) => (
              <Select
                label="Oracle Status"
                options={oracleStatusOptions}
                value={field.value}
                onChange={field.onChange}
                error={formErrors.oracle_status_code?.message}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="oracle_severity"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Oracle Severity"
                placeholder="e.g., Critical, High, Medium, Low"
              />
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="oracle_priority"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Oracle Priority"
                placeholder="e.g., 1, 2, 3, 4"
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="oracle_close_reason"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Close Reason"
                placeholder="Reason for closure (if applicable)"
              />
            )}
          />
        </div>
      </div>

      <div>
        <Controller
          name="oracle_environment"
          control={control}
          render={({ field }) => (
            <TextArea
              {...field}
              label="Environment"
              placeholder="Details about the environment where the bug occurs"
              rows={3}
            />
          )}
        />
      </div>
    </>
  );

  // GitHub Issue schema-specific fields
  const renderGitHubIssueFields = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="github_issue_number"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                type="number"
                label="GitHub Issue Number"
                placeholder="e.g., 123"
                disabled={isLoadingGitHubIssue}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="github_issue_url"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="GitHub Issue URL"
                placeholder="https://github.com/owner/repo/issues/123"
                disabled={isLoadingGitHubIssue}
              />
            )}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Controller
            name="github_repo"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Repository"
                placeholder="e.g., react"
                disabled={isLoadingGitHubIssue}
              />
            )}
          />
        </div>
        
        <div>
          <Controller
            name="github_owner"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                label="Owner"
                placeholder="e.g., facebook"
                disabled={isLoadingGitHubIssue}
              />
            )}
          />
        </div>
      </div>
      
      <div>
        <Controller
          name="github_state"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              label="Issue State"
              placeholder="e.g., open, closed"
              disabled={isLoadingGitHubIssue}
            />
          )}
        />
      </div>
      
      {githubIssueError && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {githubIssueError}
        </div>
      )}
      
      {isLoadingGitHubIssue && (
        <div className="mt-4 text-center py-4">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-gray-500">Loading GitHub issue data...</p>
        </div>
      )}
    </>
  ); // This closes renderGitHubIssueFields

  // Render schema-specific fields based on selected schema type
  const renderSchemaFields = () => {
    switch (selectedSchemaType) {
      case BugSchemaType.BASE:
        return renderBaseFields();
      case BugSchemaType.MOZILLA:
        return renderMozillaFields();
      case BugSchemaType.CHROMIUM:
        return renderChromiumFields();
      case BugSchemaType.ORACLE:
        return renderOracleFields();
      case BugSchemaType.GITHUB_ISSUE:
        return renderGitHubIssueFields();
      default:
        return renderBaseFields();
    }
  };
  
  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8 bg-white shadow-lg rounded-lg">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Bug Report</h1>
      {/* Display general submission error */} 
      {submitError && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-semibold">Error Submitting Bug:</p>
          <p>{submitError}</p>
        </div>
      )}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 divide-y divide-gray-200">
        {/* Schema Type Selector - Placed before common fields for clarity */} 
        <div className="pt-8">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">Bug Schema Type</h3>
            <p className="mt-1 text-sm text-gray-500">
              Select the type of bug report you want to create. This will tailor the available fields.
            </p>
          </div>
          <div className="mt-6">
            <Controller
              name="schema_type"
              control={control}
              rules={{ required: 'Schema type is required' }}
              render={({ field }) => (
                <Select
                  {...field}
                  label="Schema Type"
                  options={bugSchemaOptions}
                  onChange={(value: string) => { // The Select component passes the value as a string
                    const newType = value as BugSchemaType;
                    field.onChange(newType); // Pass the casted value to react-hook-form
                    handleSchemaTypeChange(newType); // Pass to custom handler
                  }}
                  value={selectedSchemaType} // Ensure this reflects the actual selected state
                  disabled={schemaTypeSelected} // Disable after first selection or GitHub import
                />
              )}
            />
            {formErrors.schema_type && <p className="mt-2 text-sm text-red-600">{formErrors.schema_type.message}</p>}
          </div>
        </div>

        {/* Common Fields - Title, Description, Reporter etc. */} 
        <div className="pt-8">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">Common Details</h3>
          </div>
          <div className="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
            <div className="sm:col-span-6">
              <Controller
                name="title"
                control={control}
                rules={{ required: 'Title is required' }}
                render={({ field }) => <Input {...field} label="Title" placeholder="Short summary of the bug" />}
              />
              {formErrors.title && <p className="mt-2 text-sm text-red-600">{formErrors.title.message}</p>}
            </div>

            <div className="sm:col-span-6">
              <Controller
                name="description"
                control={control}
                rules={{ required: 'Description is required' }}
                render={({ field }) => (
                  <TextArea
                    {...field}
                    label="Description"
                    placeholder="Detailed steps to reproduce, expected vs. actual results"
                    rows={6}
                  />
                )}
              />
              {formErrors.description && <p className="mt-2 text-sm text-red-600">{formErrors.description.message}</p>}
            </div>
            
            <div className="sm:col-span-3">
              <Controller
                name="reporter"
                control={control}
                render={({ field }) => <Input {...field} label="Reporter (Optional)" placeholder="Your name or email" />}
              />
            </div>

            <div className="sm:col-span-3">
              <Controller
                name="product"
                control={control}
                render={({ field }) => <Input {...field} label="Product (Optional)" placeholder="e.g., My Awesome App" />}
              />
            </div>

            <div className="sm:col-span-3">
              <Controller
                name="component"
                control={control}
                render={({ field }) => <Input {...field} label="Component (Optional)" placeholder="e.g., User Login Page" />}
              />
            </div>

            <div className="sm:col-span-3">
              <Controller
                name="version"
                control={control}
                render={({ field }) => <Input {...field} label="Version (Optional)" placeholder="e.g., 1.0.2" />}
              />
            </div>

            <div className="sm:col-span-3">
              <Controller
                name="platform"
                control={control}
                render={({ field }) => <Input {...field} label="Platform (Optional)" placeholder="e.g., Web, iOS, Android" />}
              />
            </div>

            <div className="sm:col-span-3">
              <Controller
                name="operating_system"
                control={control}
                render={({ field }) => <Input {...field} label="Operating System (Optional)" placeholder="e.g., Windows 11, macOS Sonoma" />}
              />
            </div>
          </div>
        </div>

        {/* Schema-specific fields */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {selectedSchemaType === BugSchemaType.BASE && 'Bug Details'}
            {selectedSchemaType === BugSchemaType.MOZILLA && 'Mozilla/Bugzilla Details'}
            {selectedSchemaType === BugSchemaType.CHROMIUM && 'Chromium Details'}
            {selectedSchemaType === BugSchemaType.ORACLE && 'Oracle Details'}
            {selectedSchemaType === BugSchemaType.GITHUB_ISSUE && 'GitHub Issue Details'}
          </h2>
          {renderSchemaFields()}
        </div>
        
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Attachments</h2>
          <FileUpload
            label="Attachments"
            multiple={true}
            accept=".jpg,.jpeg,.png,.pdf,.txt"
            onChange={onFilesSelect}
          />
          <p className="mt-1 text-xs text-gray-500">
            Supported file types: Images (.jpg, .png), PDF files, and text files
          </p>
        </div>
        
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p className="mt-1 text-xs text-gray-500 text-right">
              Uploading attachments: {uploadProgress}%
            </p>
          </div>
        )}
        
        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/bugs')}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            disabled={isSubmitting}
          >
            Submit Bug Report
          </Button>
        </div>
      </form>
    </div>
  );
}
