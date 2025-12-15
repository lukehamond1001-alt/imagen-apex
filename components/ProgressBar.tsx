
import React from 'react';

interface ProgressBarProps {
  progress: number; // 0 to 100
  label?: string;
  colorClass?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  colorClass = "bg-indigo-500"
}) => {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-xs text-zinc-400 mb-2 font-mono uppercase tracking-wider">
          <span className="flex items-center gap-2">
            {progress < 100 && <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"/>}
            {label}
          </span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ease-out ${colorClass} ${progress < 100 ? 'animate-pulse' : ''}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
