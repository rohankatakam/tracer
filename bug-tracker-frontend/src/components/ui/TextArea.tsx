import React, { forwardRef } from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, className = '', ...props }, ref) => {
    const errorClass = error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : '';
    
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={props.id} className="form-label">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={`w-full rounded-md border border-gray-300 px-4 py-2 shadow-sm focus:border-primary focus:ring-1 focus:ring-primary ${errorClass} ${className}`}
          rows={props.rows || 4}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);
