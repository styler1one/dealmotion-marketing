"use client";

import { useEffect, useState } from "react";
import { 
  Video, 
  Eye, 
  TrendingUp, 
  PlayCircle 
} from "lucide-react";
import { getDashboardStats, DashboardStats } from "@/lib/api";

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: "up" | "down" | "neutral";
  icon: React.ReactNode;
  loading?: boolean;
}

function StatCard({ title, value, change, changeType = "neutral", icon, loading }: StatCardProps) {
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
          {loading ? (
            <div className="h-8 w-16 bg-slate-700 animate-pulse rounded mt-1" />
          ) : (
            <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
          )}
          {change && !loading && (
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
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  // Count total content items from content_mix
  const totalContent = stats?.content_mix 
    ? Object.values(stats.content_mix).reduce((a, b) => a + b, 0) 
    : 0;

  const statCards = [
    {
      title: "Total Videos",
      value: stats?.total_videos?.toString() || "0",
      change: stats?.videos_this_week ? `${stats.videos_this_week} this week` : "No videos yet",
      changeType: (stats?.videos_this_week || 0) > 0 ? "up" as const : "neutral" as const,
      icon: <Video className="w-5 h-5" />,
    },
    {
      title: "Total Views",
      value: stats?.total_views ? formatNumber(stats.total_views) : "0",
      change: stats?.total_views ? "All time" : "No views yet",
      changeType: (stats?.total_views || 0) > 0 ? "up" as const : "neutral" as const,
      icon: <Eye className="w-5 h-5" />,
    },
    {
      title: "Topics Generated",
      value: totalContent.toString(),
      change: "Total content ideas",
      changeType: totalContent > 0 ? "up" as const : "neutral" as const,
      icon: <TrendingUp className="w-5 h-5" />,
    },
    {
      title: "This Week",
      value: stats?.videos_this_week?.toString() || "0",
      change: "Videos created",
      changeType: (stats?.videos_this_week || 0) > 0 ? "up" as const : "neutral" as const,
      icon: <PlayCircle className="w-5 h-5" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((stat, i) => (
        <StatCard key={i} {...stat} loading={loading} />
      ))}
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}
