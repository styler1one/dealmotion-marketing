"use client";

import { useState } from "react";
import { 
  Play, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Clock,
  ChevronDown,
  ChevronRight
} from "lucide-react";

interface PipelineRun {
  id: string;
  date: string;
  status: "completed" | "failed" | "running";
  duration?: string;
  stepsCompleted: number;
  totalSteps: number;
}

function RunCard({ run }: { run: PipelineRun }) {
  const [expanded, setExpanded] = useState(false);
  
  const statusConfig = {
    completed: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    failed: { icon: XCircle, color: "text-red-400", bg: "bg-red-500/10" },
    running: { icon: RefreshCw, color: "text-amber-400", bg: "bg-amber-500/10" },
  };
  
  const config = statusConfig[run.status];
  const StatusIcon = config.icon;

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
            <p className="font-medium text-slate-200">{run.date}</p>
            <p className="text-sm text-slate-500">
              {run.stepsCompleted}/{run.totalSteps} steps • {run.duration || "In progress..."}
            </p>
          </div>
        </div>
        {expanded ? (
          <ChevronDown className="w-5 h-5 text-slate-500" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-500" />
        )}
      </button>
      
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-400">
            Pipeline trace details will appear here once runs are available.
          </p>
        </div>
      )}
    </div>
  );
}

export default function PipelinePage() {
  // TODO: Fetch real data from API
  const runs: PipelineRun[] = [];

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
        <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-medium rounded-lg transition-colors">
          <Play className="w-4 h-4" />
          Trigger Run
        </button>
      </header>

      {/* Today's Run Status */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Today's Run</h2>
        <div className="card">
          <div className="flex items-center justify-center py-12 text-center">
            <div>
              <Clock className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No run scheduled for today</p>
              <p className="text-sm text-slate-500 mt-1">
                Click "Trigger Run" to start the pipeline manually
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Run History */}
      <section>
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Run History</h2>
        
        {runs.length === 0 ? (
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
          runs.map((run) => <RunCard key={run.id} run={run} />)
        )}
      </section>
    </div>
  );
}

