import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  message,
  onDismiss,
  className = '',
}) => {
  return (
    <div
      className={`p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-between gap-3 shadow-lg shadow-rose-950/20 ${className}`}
    >
      <div className="flex items-center gap-2.5">
        <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
        <span className="font-medium">{message}</span>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="p-1 rounded hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
