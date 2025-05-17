'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { Input } from '../../../components/ui/Input';
import { TextArea } from '../../../components/ui/TextArea';
import { Select } from '../../../components/ui/Select';
import { Button } from '../../../components/ui/Button';
import { FileUpload } from '../../../components/ui/FileUpload';
import {
  CreateBugRequest, BugSchemaType, 
  BaseSeverity, BaseStatus,
  MozillaSeverity, MozillaPriority, MozillaStatus, MozillaResolution,
  ChromiumPriority, ChromiumType, ChromiumStatus,
  BaseTypeCreateRequest, MozillaCreateRequest, ChromiumCreateRequest, OracleCreateRequest
} from '../../../types/bug';
import { bugAPI, attachmentAPI } from '../../../services/api-client';

// Bug schema type options
const schemaTypeOptions = [
  { value: BugSchemaType.BASE, label: 'Base' },
  { value: BugSchemaType.MOZILLA, label: 'Mozilla/Bugzilla' },
  { value: BugSchemaType.CHROMIUM, label: 'Chromium Issue' },
  { value: BugSchemaType.ORACLE, label: 'Oracle' },
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [selectedSchemaType, setSelectedSchemaType] = useState<BugSchemaType>(BugSchemaType.BASE);
  const [schemaTypeSelected, setSchemaTypeSelected] = useState<boolean>(false);
  
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
      
      default:
        return {
          ...commonDefaults,
          schema_type: BugSchemaType.BASE,
          severity: BaseSeverity.MEDIUM,
        } as BaseTypeCreateRequest;
    }
  };
  
  // Define a type that includes all possible error fields from all bug schema types
  type BugFormErrors = {
    [key: string]: any; // This allows access to any property with string access
  };
  
  const { 
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<CreateBugRequest>({
    defaultValues: getDefaultValues(),
  });
  
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
    } catch (error) {
      console.error('Error creating bug:', error);
      setSubmitError('Failed to create bug. Please try again.');
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
      default:
        return renderBaseFields();
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Report New Bug</h1>
      
      {submitError && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {submitError}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Common fields for all bug schemas */}
        {renderCommonFields()}
        
        {/* Schema-specific fields */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {selectedSchemaType === BugSchemaType.BASE && 'Bug Details'}
            {selectedSchemaType === BugSchemaType.MOZILLA && 'Mozilla/Bugzilla Details'}
            {selectedSchemaType === BugSchemaType.CHROMIUM && 'Chromium Details'}
            {selectedSchemaType === BugSchemaType.ORACLE && 'Oracle Details'}
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
