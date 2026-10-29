import React from 'react';

interface Props {
  status: string;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const norm = status.toUpperCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';

  if (['SUCCEEDED', 'APPROVED', 'COMPLETED', 'PAID', 'RESOLVED', 'ACTIVE'].includes(norm)) {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['DECLINED', 'REJECTED', 'FAILED'].includes(norm)) {
    styles = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (['PENDING', 'AUTHENTICATION_REQUIRED', 'INVESTIGATING', 'REVIEW'].includes(norm)) {
    styles = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (['PROCESSING', 'QUEUED'].includes(norm)) {
    styles = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (['SUSPENDED', 'CANCELLED'].includes(norm)) {
    styles = 'bg-purple-50 text-purple-700 border-purple-200';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles}`}
    >
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current opacity-75"></span>
      {norm}
    </span>
  );
};
