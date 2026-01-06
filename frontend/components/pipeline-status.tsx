"use client";

import { 
  Lightbulb, 
  FileText, 
  Search, 
  Shield, 
  Mic, 
  Image, 
  Film, 
  Youtube,
  CheckCircle2,
  Circle,
  Loader2,
  XCircle
} from "lucide-react";

type StepStatus = "pending" | "running" | "completed" | "failed";

interface PipelineStep {
  id: number;
  name: string;
  icon: React.ReactNode;
  status: StepStatus;
  output?: string;
}

const statusConfig = {
  pending: {
    icon: Circle,
    color: "text-slate-500",
    bgColor: "bg-slate-500/10",
  },
  running: {
    icon: Loader2,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
  },
  completed: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
  },
  failed: {
    icon: XCircle,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
  },
};

function StepIndicator({ step }: { step: PipelineStep }) {
  const config = statusConfig[step.status];
  const StatusIcon = config.icon;
  
  return (
    <div className="flex items-center gap-4 p-4 rounded-lg bg-surface hover:bg-surface-lighter transition-colors">
      <div className={`p-2 rounded-lg ${config.bgColor}`}>
        <div className={config.color}>
          {step.icon}
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-200">{step.name}</span>
          <StatusIcon 
            className={`w-4 h-4 ${config.color} ${step.status === "running" ? "animate-spin" : ""}`} 
          />
        </div>
        {step.output && (
          <p className="text-xs text-slate-500 truncate mt-1">{step.output}</p>
        )}
      </div>
    </div>
  );
}

export function PipelineStatus() {
  // TODO: Fetch real pipeline status from API
  const todayRun = null; // No run yet
  
  const steps: PipelineStep[] = [
    { id: 1, name: "Topic Generation", icon: <Lightbulb className="w-4 h-4" />, status: "pending" },
    { id: 2, name: "Script Writing", icon: <FileText className="w-4 h-4" />, status: "pending" },
    { id: 3, name: "SEO Optimization", icon: <Search className="w-4 h-4" />, status: "pending" },
    { id: 4, name: "QC Gate", icon: <Shield className="w-4 h-4" />, status: "pending" },
    { id: 5, name: "Voice Generation", icon: <Mic className="w-4 h-4" />, status: "pending" },
    { id: 6, name: "Thumbnail", icon: <Image className="w-4 h-4" />, status: "pending" },
    { id: 7, name: "Video Generation", icon: <Film className="w-4 h-4" />, status: "pending" },
    { id: 8, name: "YouTube Upload", icon: <Youtube className="w-4 h-4" />, status: "pending" },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Today's Pipeline</h2>
          <p className="text-sm text-slate-500 mt-1">
            {todayRun ? `Run ID: ${todayRun}` : "No run scheduled yet"}
          </p>
        </div>
        <button className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-lg transition-colors">
          Run Now
        </button>
      </div>

      <div className="space-y-2">
        {steps.map((step) => (
          <StepIndicator key={step.id} step={step} />
        ))}
      </div>

      {/* Progress bar */}
      <div className="mt-6 pt-4 border-t border-slate-700">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-400">Progress</span>
          <span className="text-slate-300">0 / 8 steps</span>
        </div>
        <div className="h-2 bg-surface rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-500"
            style={{ width: "0%" }}
          />
        </div>
      </div>
    </div>
  );
}

