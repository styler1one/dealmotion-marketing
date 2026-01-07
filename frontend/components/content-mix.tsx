"use client";

import { useEffect, useState } from "react";
import { getContentMix } from "@/lib/api";

// Color mapping for thought leadership content types
const TYPE_COLORS: Record<string, string> = {
  sales_illusion: "bg-red-500",
  execution_failure: "bg-orange-500",
  signal_miss: "bg-amber-500",
  system_flaw: "bg-blue-500",
  decision_dynamics: "bg-purple-500",
  // Fallback for any unknown types
  default: "bg-slate-500",
};

// Human-readable labels for content types
const TYPE_LABELS: Record<string, string> = {
  sales_illusion: "Sales Illusions",
  execution_failure: "Execution Failures",
  signal_miss: "Signal Misses",
  system_flaw: "System Flaws",
  decision_dynamics: "Decision Dynamics",
};

interface ContentTypeData {
  type: string;
  label: string;
  color: string;
  count: number;
  percentage: number;
}

export function ContentMix() {
  const [contentMix, setContentMix] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchContentMix() {
      try {
        const data = await getContentMix();
        setContentMix(data.content_mix || {});
        setError(null);
      } catch (err) {
        console.error("Failed to fetch content mix:", err);
        setError("Failed to load");
        setContentMix({});
      } finally {
        setLoading(false);
      }
    }
    fetchContentMix();
  }, []);

  const total = Object.values(contentMix).reduce((sum, count) => sum + count, 0);

  // Build content types dynamically from the data
  const contentTypes: ContentTypeData[] = Object.entries(contentMix)
    .map(([type, count]) => ({
      type,
      label: TYPE_LABELS[type] || type.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
      color: TYPE_COLORS[type] || TYPE_COLORS.default,
      count,
      percentage: total > 0 ? Math.round((count / total) * 100) : 0,
    }))
    .sort((a, b) => b.count - a.count); // Sort by count descending

  return (
    <div className="card h-full">
      <div className="card-header">
        <h2 className="card-title">Content Mix</h2>
        <span className="text-xs text-slate-500">
          {total} total
        </span>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="flex items-center justify-between mb-2">
                <div className="h-4 w-24 bg-slate-700 rounded" />
                <div className="h-4 w-16 bg-slate-700 rounded" />
              </div>
              <div className="h-2 bg-slate-700 rounded-full" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="py-8 text-center text-slate-500">
          <p>{error}</p>
        </div>
      ) : contentTypes.length === 0 ? (
        <div className="py-8 text-center text-slate-500">
          <p>No content generated yet</p>
          <p className="text-xs mt-2">Run the pipeline to generate topics</p>
        </div>
      ) : (
        <div className="space-y-4">
          {contentTypes.map((type) => (
            <div key={type.type}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-300">{type.label}</span>
                <span className="text-sm text-slate-500">
                  {type.count} ({type.percentage}%)
                </span>
              </div>
              <div className="h-2 bg-surface rounded-full overflow-hidden">
                <div 
                  className={`h-full ${type.color} transition-all duration-500`}
                  style={{ width: `${type.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-500">
          Thought leadership content distribution
        </p>
      </div>
    </div>
  );
}
