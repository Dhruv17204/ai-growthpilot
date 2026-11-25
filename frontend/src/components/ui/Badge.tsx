import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'high' | 'medium' | 'low' | 'neutral' | 'success' | 'warning' | 'purple';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md'
}) => {
  const variantStyles = {
    high: 'bg-violet-100 text-violet-800 border-violet-200 font-semibold',
    medium: 'bg-amber-100 text-amber-800 border-amber-200 font-semibold',
    low: 'bg-slate-100 text-slate-600 border-slate-200 font-medium',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    warning: 'bg-amber-100 text-amber-800 border-amber-200',
    purple: 'bg-indigo-100 text-indigo-800 border-indigo-200 font-medium'
  }[variant];

  const sizeStyles = {
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1'
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border ${variantStyles} ${sizeStyles} tracking-tight`}
    >
      {children}
    </span>
  );
};
