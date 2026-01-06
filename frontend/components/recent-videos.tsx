"use client";

import { ExternalLink, Play, Eye, Clock } from "lucide-react";

interface Video {
  id: string;
  title: string;
  type: string;
  status: "published" | "processing" | "queued";
  views?: number;
  retention?: number;
  publishedAt?: string;
  youtubeUrl?: string;
}

function VideoCard({ video }: { video: Video }) {
  const statusColors = {
    published: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    processing: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    queued: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg bg-surface hover:bg-surface-lighter transition-colors">
      {/* Thumbnail placeholder */}
      <div className="w-32 h-20 bg-surface-lighter rounded-lg flex items-center justify-center">
        <Play className="w-8 h-8 text-slate-600" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="font-medium text-slate-200 truncate">{video.title}</h3>
          <span className={`px-2 py-0.5 text-xs rounded-full border ${statusColors[video.status]}`}>
            {video.status}
          </span>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <span className="capitalize">{video.type.replace("_", " ")}</span>
          {video.views !== undefined && (
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {video.views.toLocaleString()}
            </span>
          )}
          {video.retention !== undefined && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {video.retention}% retention
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      {video.youtubeUrl && (
        <a
          href={video.youtubeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 text-slate-400 hover:text-brand-400 transition-colors"
        >
          <ExternalLink className="w-5 h-5" />
        </a>
      )}
    </div>
  );
}

export function RecentVideos() {
  // TODO: Fetch real data from API
  const videos: Video[] = [];

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Recent Videos</h2>
        <a href="/content" className="text-sm text-brand-400 hover:text-brand-300">
          View all →
        </a>
      </div>

      {videos.length === 0 ? (
        <div className="py-12 text-center">
          <Play className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No videos yet</p>
          <p className="text-sm text-slate-500 mt-1">
            Run the pipeline to generate your first video
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      )}
    </div>
  );
}

