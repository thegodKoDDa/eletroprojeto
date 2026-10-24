import type { HTMLAttributes } from 'react';

export type FeedbackTone = 'info' | 'success' | 'warning' | 'error';

export function Feedback({
  tone = 'info',
  children,
  className = '',
  role,
  ...props
}: HTMLAttributes<HTMLDivElement> & { tone?: FeedbackTone }) {
  return (
    <div
      {...props}
      className={`feedback ${className}`}
      data-tone={tone}
      role={role ?? (tone === 'error' ? 'alert' : 'status')}
    >
      {children}
    </div>
  );
}
