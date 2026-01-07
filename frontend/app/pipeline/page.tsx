"use client";

import { useEffect, useState } from "react";
import { 
  Play, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Clock,
  ChevronDown,
  ChevronRight,
  Loader2,
  Lightbulb,
  FileText,
  Mic,
  Film,
  Youtube
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PipelineRun {
  id: string;
  run_date: string;
  status: string;
  topics_generated: number;
  scripts_generated: number;
  videos_created: number;
  videos_uploaded: number;
  started_at: string;
  completed_at: string | null;
  errors?: string[];
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("nl-NL", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(start: string, end: string | null): string {
  if (!end) return "In progress...";
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${seconds % 60}s`;
}

function RunCard({ run }: { run: PipelineRun }) {
  const [expanded, setExpanded] = useState(false);
  
  const statusConfig: Record<string, { icon: typeof CheckCircle2; color: string; bg: string }> = {
    completed: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    failed: { icon: XCircle, color: "text-red-400", bg: "bg-red-500/10" },
    running: { icon: Loader2, color: "text-amber-400", bg: "bg-amber-500/10" },
  };
  
  const config = statusConfig[run.status] || statusConfig.running;
  const StatusIcon = config.icon;

  const steps = [
    { name: "Topics", count: run.topics_generated, icon: Lightbulb },
    { name: "Scripts", count: run.scripts_generated, icon: FileText },
    { name: "Videos", count: run.videos_created, icon: Film },
    { name: "Uploads", count: run.videos_uploaded, icon: Youtube },
  ];

  return (
    <div className="card mb-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <div className={`p-2 rounded-lg ${config.bg}`}>
            <StatusIcon className={`w-5 h-5 ${config.color} ${run.status === "running" ? "animate-spin" : ""}`} />
          </div>
          <div className="text-left">
            <p className="font-medium text-slate-200">{formatDate(run.started_at)}</p>
            <p className="text-sm text-slate-500">
              {formatDuration(run.started_at, run.completed_at)} • {run.status}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            {steps.map((step) => (
              <span key={step.name} className="flex items-center gap-1" title={step.name}>
                <step.icon className="w-3 h-3" />
                {step.count}
              </span>
            ))}
          </div>
          {expanded ? (
            <ChevronDown className="w-5 h-5 text-slate-500" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-500" />
          )}
        </div>
      </button>
      
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {steps.map((step) => (
              <div key={step.name} className="bg-slate-800/50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <step.icon className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-400">{step.name}</span>
                </div>
                <p className="text-xl font-bold text-slate-200">{step.count}</p>
              </div>
            ))}
          </div>
          {run.errors && run.errors.length > 0 && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400 font-medium mb-1">Errors:</p>
              {run.errors.map((error, i) => (
                <p key={i} className="text-xs text-red-300">{error}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PipelinePage() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  async function fetchRuns() {
    try {
      const response = await fetch(`${API_URL}/api/dashboard/pipeline-runs?limit=20`);
      if (response.ok) {
        const data = await response.json();
        setRuns(data.runs || []);
      }
    } catch (error) {
      console.error("Failed to fetch pipeline runs:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRuns();
  }, []);

  async function triggerPipeline() {
    setTriggering(true);
    try {
      const response = await fetch(`${API_URL}/api/pipeline/trigger-test`, {
        method: "POST",
      });
      if (response.ok) {
        // Refresh runs after a delay
        setTimeout(fetchRuns, 3000);
      }
    } catch (error) {
      console.error("Failed to trigger pipeline:", error);
    } finally {
      setTriggering(false);
    }
  }

  const todayRun = runs.find(r => {
    const today = new Date().toISOString().split("T")[0];
    return r.run_date === today || r.started_at.startsWith(today);
  });

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Pipeline</h1>
          <p className="text-slate-400 mt-1">
            View and manage content generation runs
          </p>
        </div>
        <button 
          onClick={triggerPipeline}
          disabled={triggering}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:bg-brand-700 text-white font-medium rounded-lg transition-colors"
        >
          {triggering ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Trigger Run
            </>
          )}
        </button>
      </header>

      {/* Today's Run Status */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Today's Run</h2>
        {todayRun ? (
          <RunCard run={todayRun} />
        ) : (
          <div className="card">
            <div className="flex items-center justify-center py-12 text-center">
              <div>
                <Clock className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No run today yet</p>
                <p className="text-sm text-slate-500 mt-1">
                  Daily pipeline runs at 10:00 AM or click "Trigger Run"
                </p>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Run History */}
      <section>
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Run History</h2>
        
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-slate-700 rounded-lg" />
                  <div className="flex-1">
                    <div className="h-4 w-32 bg-slate-700 rounded mb-2" />
                    <div className="h-3 w-24 bg-slate-700 rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : runs.length === 0 ? (
          <div className="card">
            <div className="py-12 text-center">
              <RefreshCw className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No pipeline runs yet</p>
              <p className="text-sm text-slate-500 mt-1">
                Runs will appear here after the first execution
              </p>
            </div>
          </div>
        ) : (
          runs.filter(r => r !== todayRun).map((run) => <RunCard key={run.id} run={run} />)
        )}
      </section>
    </div>
  );
}
