"use client";

import { useEffect, useState } from "react";
import { BarChart3, TrendingUp, Eye, Users, Clock, ThumbsUp } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Stats {
  total_videos: number;
  total_views: number;
  videos_this_week: number;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch(`${API_URL}/api/dashboard/stats`);
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  const statCards = [
    {
      title: "Total Videos",
      value: stats?.total_videos || 0,
      icon: <BarChart3 className="w-5 h-5" />,
      color: "text-brand-400",
      bgColor: "bg-brand-500/10",
    },
    {
      title: "Total Views",
      value: stats?.total_views || 0,
      icon: <Eye className="w-5 h-5" />,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
    },
    {
      title: "This Week",
      value: stats?.videos_this_week || 0,
      icon: <TrendingUp className="w-5 h-5" />,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
  ];

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Analytics</h1>
        <p className="text-slate-400 mt-1">
          Performance metrics and insights
        </p>
      </header>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {statCards.map((stat, i) => (
          <div key={i} className="card">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <div className={stat.color}>{stat.icon}</div>
              </div>
              <div>
                <p className="text-sm text-slate-400">{stat.title}</p>
                {loading ? (
                  <div className="h-7 w-16 bg-slate-700 animate-pulse rounded mt-1" />
                ) : (
                  <p className="text-2xl font-bold text-slate-100">
                    {stat.value.toLocaleString()}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Coming Soon */}
      <div className="card">
        <div className="py-16 text-center">
          <BarChart3 className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">
            Detailed Analytics Coming Soon
          </h3>
          <p className="text-slate-500 max-w-md mx-auto">
            YouTube Analytics integration will show retention rates, 
            engagement metrics, and performance trends over time.
          </p>
        </div>
      </div>

      {/* Planned Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        {[
          { icon: <Clock className="w-5 h-5" />, label: "Avg. Watch Time", status: "Coming" },
          { icon: <Users className="w-5 h-5" />, label: "Subscribers Gained", status: "Coming" },
          { icon: <ThumbsUp className="w-5 h-5" />, label: "Engagement Rate", status: "Coming" },
          { icon: <TrendingUp className="w-5 h-5" />, label: "Growth Trend", status: "Coming" },
        ].map((item, i) => (
          <div key={i} className="card opacity-50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-700/50 rounded-lg text-slate-500">
                {item.icon}
              </div>
              <div>
                <p className="text-sm text-slate-400">{item.label}</p>
                <p className="text-xs text-slate-600">{item.status}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

