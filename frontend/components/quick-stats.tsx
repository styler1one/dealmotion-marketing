"use client";

import { 
  Video, 
  Eye, 
  TrendingUp, 
  Users 
} from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: "up" | "down" | "neutral";
  icon: React.ReactNode;
}

function StatCard({ title, value, change, changeType = "neutral", icon }: StatCardProps) {
  const changeColor = {
    up: "text-emerald-400",
    down: "text-red-400",
    neutral: "text-slate-400",
  }[changeType];

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
          {change && (
            <p className={`text-xs mt-2 ${changeColor}`}>
              {changeType === "up" && "↑ "}
              {changeType === "down" && "↓ "}
              {change}
            </p>
          )}
        </div>
        <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400">
          {icon}
        </div>
      </div>
    </div>
  );
}

export function QuickStats() {
  // TODO: Fetch real data from API
  const stats = [
    {
      title: "Videos This Week",
      value: "0",
      change: "Pipeline not started",
      changeType: "neutral" as const,
      icon: <Video className="w-5 h-5" />,
    },
    {
      title: "Total Views (7d)",
      value: "—",
      change: "No data yet",
      changeType: "neutral" as const,
      icon: <Eye className="w-5 h-5" />,
    },
    {
      title: "Avg. Retention",
      value: "—",
      change: "No data yet",
      changeType: "neutral" as const,
      icon: <TrendingUp className="w-5 h-5" />,
    },
    {
      title: "New Subscribers",
      value: "—",
      change: "No data yet",
      changeType: "neutral" as const,
      icon: <Users className="w-5 h-5" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <StatCard key={i} {...stat} />
      ))}
    </div>
  );
}

