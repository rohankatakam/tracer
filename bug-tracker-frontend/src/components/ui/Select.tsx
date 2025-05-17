import React, { forwardRef } from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  options: SelectOption[];
  error?: string;
  helpText?: string;
  onChange?: (value: string) => void;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, error, helpText, onChange, className = '', ...props }, ref) => {
    const errorClass = error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : '';
    
    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (onChange) {
        onChange(e.target.value);
      }
    };
    
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={props.id} className="form-label">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={`w-full rounded-md border border-gray-300 px-4 py-2 shadow-sm focus:border-primary focus:ring-1 focus:ring-primary ${errorClass} ${className}`}
          onChange={handleChange}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
        {helpText && !error && (
          <p className="mt-1 text-xs text-gray-500">{helpText}</p>
        )}
      </div>
    );
  }
);
