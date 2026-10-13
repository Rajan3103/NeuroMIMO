import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Processing...',
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 p-6 text-slate-400 ${className}`}>
      <Loader2 className={`${sizeClasses[size]} animate-spin text-cyan-400`} />
      {label && <span className="text-xs font-medium tracking-wide">{label}</span>}
    </div>
  );
};
