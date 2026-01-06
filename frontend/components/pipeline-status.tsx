"use client";

import { useEffect, useState } from "react";
import { 
  Lightbulb, 
  FileText, 
  Mic, 
  Film, 
  Youtube,
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Sparkles,
  Play
} from "lucide-react";
import { getLatestPipelineRun, PipelineRunItem } from "@/lib/api";

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
  const [latestRun, setLatestRun] = useState<PipelineRunItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    async function fetchLatestRun() {
      try {
        const data = await getLatestPipelineRun();
        setLatestRun(data.run);
      } catch (error) {
        console.error("Failed to fetch pipeline run:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchLatestRun();
  }, []);

  const triggerPipeline = async () => {
    setTriggering(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/api/pipeline/trigger-test`, {
        method: "POST",
      });
      if (response.ok) {
        // Refresh data after a short delay
        setTimeout(async () => {
          const data = await getLatestPipelineRun();
          setLatestRun(data.run);
        }, 2000);
      }
    } catch (error) {
      console.error("Failed to trigger pipeline:", error);
    } finally {
      setTriggering(false);
    }
  };

  // Determine step status based on latestRun
  const getStepStatus = (stepIndex: number): StepStatus => {
    if (!latestRun) return "pending";
    
    const { status, topics_generated, scripts_generated, videos_created, videos_uploaded } = latestRun;
    
    if (status === "running") {
      // Determine which step is running
      if (topics_generated === 0) return stepIndex === 0 ? "running" : "pending";
      if (scripts_generated === 0) return stepIndex <= 0 ? "completed" : stepIndex === 1 ? "running" : "pending";
      if (videos_created === 0) return stepIndex <= 2 ? "completed" : stepIndex === 3 ? "running" : "pending";
      if (videos_uploaded === 0) return stepIndex <= 3 ? "completed" : stepIndex === 4 ? "running" : "pending";
      return "running";
    }
    
    if (status === "completed") return "completed";
    if (status === "failed") {
      // Mark last step as failed
      if (videos_uploaded === 0 && videos_created > 0) return stepIndex === 4 ? "failed" : stepIndex < 4 ? "completed" : "pending";
      return stepIndex === 0 ? "failed" : "pending";
    }
    
    return "pending";
  };

  const steps: PipelineStep[] = [
    { id: 1, name: "Topic Generation", icon: <Lightbulb className="w-4 h-4" />, status: getStepStatus(0) },
    { id: 2, name: "Script Writing", icon: <FileText className="w-4 h-4" />, status: getStepStatus(1) },
    { id: 3, name: "Voice Generation", icon: <Mic className="w-4 h-4" />, status: getStepStatus(2) },
    { id: 4, name: "Video Generation", icon: <Film className="w-4 h-4" />, status: getStepStatus(3) },
    { id: 5, name: "YouTube Upload", icon: <Youtube className="w-4 h-4" />, status: getStepStatus(4) },
  ];

  const completedSteps = steps.filter(s => s.status === "completed").length;
  const progress = (completedSteps / steps.length) * 100;

  const runDate = latestRun?.run_date 
    ? new Date(latestRun.run_date).toLocaleDateString("nl-NL", {
        weekday: "short",
        day: "numeric",
        month: "short",
      })
    : null;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Pipeline Status</h2>
          <p className="text-sm text-slate-500 mt-1">
            {loading ? (
              "Loading..."
            ) : latestRun ? (
              <>
                {runDate} • {latestRun.status === "completed" ? "✓ Completed" : latestRun.status === "running" ? "⏳ Running..." : latestRun.status === "failed" ? "✗ Failed" : "Pending"}
              </>
            ) : (
              "No runs yet"
            )}
          </p>
        </div>
        <button 
          onClick={triggerPipeline}
          disabled={triggering || latestRun?.status === "running"}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
        >
          {triggering ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting...
            </>
          ) : latestRun?.status === "running" ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Pipeline
            </>
          )}
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4 p-4 rounded-lg bg-surface animate-pulse">
              <div className="w-10 h-10 bg-slate-700 rounded-lg" />
              <div className="flex-1">
                <div className="h-4 w-32 bg-slate-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {steps.map((step) => (
            <StepIndicator key={step.id} step={step} />
          ))}
        </div>
      )}

      {/* Progress bar */}
      <div className="mt-6 pt-4 border-t border-slate-700">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-400">Progress</span>
          <span className="text-slate-300">{completedSteps} / {steps.length} steps</span>
        </div>
        <div className="h-2 bg-surface rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Last result */}
      {latestRun && latestRun.status === "completed" && (
        <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <div className="flex items-center gap-2 text-emerald-400 text-sm">
            <Sparkles className="w-4 h-4" />
            <span>
              Generated {latestRun.topics_generated} topic, {latestRun.videos_created} video, {latestRun.videos_uploaded} uploaded
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
