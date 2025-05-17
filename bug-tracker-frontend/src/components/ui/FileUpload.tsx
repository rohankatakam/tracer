import React, { useState, useRef } from 'react';
import { Button } from './Button';

interface FileUploadProps {
  label?: string;
  accept?: string;
  multiple?: boolean;
  onChange: (files: File[]) => void;
  error?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  label = 'Upload Files',
  accept,
  multiple = false,
  onChange,
  error,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const fileList = Array.from(e.target.files);
      setSelectedFiles(fileList);
      onChange(fileList);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const removeFile = (index: number) => {
    const newFiles = [...selectedFiles];
    newFiles.splice(index, 1);
    setSelectedFiles(newFiles);
    onChange(newFiles);
  };

  return (
    <div className="w-full">
      {label && <label className="form-label">{label}</label>}
      
      <div className="mt-1 flex items-center">
        <Button 
          type="button" 
          variant="outline" 
          onClick={handleButtonClick}
        >
          {label}
        </Button>
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={accept}
          multiple={multiple}
        />
      </div>
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      
      {selectedFiles.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700">Selected Files:</h4>
          <ul className="mt-2 space-y-2">
            {selectedFiles.map((file, index) => (
              <li key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex-1 truncate">
                  <span className="text-sm font-medium text-gray-900">{file.name}</span>
                  <span className="ml-2 text-xs text-gray-500">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="ml-2 text-red-600 hover:text-red-900"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
