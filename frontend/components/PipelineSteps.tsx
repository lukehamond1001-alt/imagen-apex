
import React from 'react';
import { PipelineStage } from '../types';
import { Palette, Box, CheckCircle2, ChevronRight } from 'lucide-react';

interface PipelineStepsProps {
  stage: PipelineStage;
}

export const PipelineSteps: React.FC<PipelineStepsProps> = ({ stage }) => {
  
  const getStepStatus = (stepStage: PipelineStage) => {
    const stages = [
      PipelineStage.IDLE,
      PipelineStage.GENERATING_IMAGE,
      PipelineStage.IMAGE_READY,
      PipelineStage.CONVERTING_3D,
      PipelineStage.COMPLETE
    ];
    
    const currentIndex = stages.indexOf(stage);
    const stepIndex = stages.indexOf(stepStage);
    
    if (stage === PipelineStage.ERROR) return 'text-red-500 opacity-50';
    if (currentIndex > stepIndex) return 'text-green-400';
    if (currentIndex === stepIndex) return 'text-indigo-400 animate-pulse';
    return 'text-zinc-600';
  };

  return (
    <div className="flex items-center justify-between w-full px-2 py-3 bg-zinc-950/50 rounded-xl border border-zinc-800">
      
      {/* Step 1: Artist */}
      <div className={`flex items-center space-x-3 ${getStepStatus(PipelineStage.GENERATING_IMAGE)}`}>
        <div className={`p-1.5 rounded-lg border bg-zinc-900/50 ${
          stage === PipelineStage.GENERATING_IMAGE ? 'border-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.2)]' : 'border-zinc-800'
        }`}>
          <Palette size={14} />
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest font-bold">Concept</span>
      </div>

      <ChevronRight size={14} className="text-zinc-800" />

      {/* Step 2: Sculptor */}
      <div className={`flex items-center space-x-3 ${getStepStatus(PipelineStage.CONVERTING_3D)}`}>
         <div className={`p-1.5 rounded-lg border bg-zinc-900/50 ${
           stage === PipelineStage.CONVERTING_3D ? 'border-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.2)]' : 'border-zinc-800'
        }`}>
          <Box size={14} />
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest font-bold">Sculpt</span>
      </div>

       <ChevronRight size={14} className="text-zinc-800" />

      {/* Step 3: Result */}
      <div className={`flex items-center space-x-3 ${getStepStatus(PipelineStage.COMPLETE)}`}>
         <div className={`p-1.5 rounded-lg border bg-zinc-900/50 ${
           stage === PipelineStage.COMPLETE ? 'border-green-500 shadow-[0_0_10px_rgba(34,197,94,0.2)]' : 'border-zinc-800'
        }`}>
          <CheckCircle2 size={14} />
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest font-bold">Ready</span>
      </div>

    </div>
  );
};
