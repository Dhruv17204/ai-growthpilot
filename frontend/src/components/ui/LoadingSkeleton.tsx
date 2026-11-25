import React from 'react';

export const LoadingSkeleton: React.FC<{ className?: string; count?: number }> = ({
  className = 'h-4 w-full',
  count = 1
}) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse rounded-md bg-slate-200/80 ${className}`}
        />
      ))}
    </div>
  );
};
