'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { Input } from '../../../components/ui/Input';
import { TextArea } from '../../../components/ui/TextArea';
import { Select } from '../../../components/ui/Select';
import { Button } from '../../../components/ui/Button';
import { FileUpload } from '../../../components/ui/FileUpload';
import { CreateBugRequest, SeverityLevel } from '../../../types/bug';
import { bugAPI, attachmentAPI } from '../../../services/api-client';

const severityOptions = [
  { value: SeverityLevel.LOW, label: 'Low' },
  { value: SeverityLevel.MEDIUM, label: 'Medium' },
  { value: SeverityLevel.HIGH, label: 'High' },
  { value: SeverityLevel.CRITICAL, label: 'Critical' },
];

export default function CreateBugPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  
  const { 
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateBugRequest>({
    defaultValues: {
      title: '',
      description: '',
      reporter: '',
      severity: SeverityLevel.MEDIUM,
    },
  });

  const onFilesSelect = (files: File[]) => {
    setSelectedFiles(files);
  };

  const onSubmit = async (data: CreateBugRequest) => {
    try {
      setIsSubmitting(true);
      setSubmitError(null);
      
      // Step 1: Create the bug
      const newBug = await bugAPI.createBug(data);
      
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

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Report New Bug</h1>
      
      {submitError && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {submitError}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
                error={errors.title?.message}
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
                error={errors.description?.message}
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
              name="severity"
              control={control}
              rules={{ required: 'Severity is required' }}
              render={({ field }) => (
                <Select
                  label="Severity"
                  options={severityOptions}
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.severity?.message}
                />
              )}
            />
          </div>
        </div>
        
        <div>
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
