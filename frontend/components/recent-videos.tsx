"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Play, Eye, ThumbsUp, MessageCircle } from "lucide-react";
import { getRecentVideos, VideoItem } from "@/lib/api";
import Image from "next/image";

function VideoCard({ video }: { video: VideoItem }) {
  const publishedDate = video.published_at 
    ? new Date(video.published_at).toLocaleDateString("nl-NL", {
        day: "numeric",
        month: "short",
      })
    : null;

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg bg-surface hover:bg-surface-lighter transition-colors">
      {/* Thumbnail */}
      <div className="w-32 h-20 bg-surface-lighter rounded-lg flex items-center justify-center overflow-hidden relative flex-shrink-0">
        {video.thumbnail_url ? (
          <Image
            src={video.thumbnail_url}
            alt={video.title}
            fill
            className="object-cover"
          />
        ) : (
          <Play className="w-8 h-8 text-slate-600" />
        )}
        {video.is_short && (
          <span className="absolute bottom-1 right-1 bg-red-600 text-white text-[10px] px-1 rounded">
            SHORT
          </span>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h3 className="font-medium text-slate-200 truncate mb-1">{video.title}</h3>
        
        <div className="flex items-center gap-4 text-sm text-slate-500">
          {publishedDate && <span>{publishedDate}</span>}
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            {video.views.toLocaleString()}
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-3 h-3" />
            {video.likes.toLocaleString()}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle className="w-3 h-3" />
            {video.comments.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Actions */}
      {video.youtube_url && (
        <a
          href={video.youtube_url}
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
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchVideos() {
      try {
        const data = await getRecentVideos(5);
        setVideos(data.videos || []);
      } catch (error) {
        console.error("Failed to fetch videos:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchVideos();
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Recent Videos</h2>
        <a href="/content" className="text-sm text-brand-400 hover:text-brand-300">
          View all →
        </a>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 p-4 rounded-lg bg-surface animate-pulse">
              <div className="w-32 h-20 bg-slate-700 rounded-lg" />
              <div className="flex-1">
                <div className="h-4 w-48 bg-slate-700 rounded mb-2" />
                <div className="h-3 w-32 bg-slate-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : videos.length === 0 ? (
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
