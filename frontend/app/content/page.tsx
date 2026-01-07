"use client";

import { useEffect, useState } from "react";
import { Video, FileText, Lightbulb, ExternalLink, Eye, ThumbsUp } from "lucide-react";
import Image from "next/image";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface VideoItem {
  id: string;
  youtube_id: string;
  youtube_url: string;
  title: string;
  thumbnail_url: string;
  views: number;
  likes: number;
  published_at: string;
}

interface Topic {
  id: string;
  title: string;
  content_type: string;
  hook: string;
  status: string;
  created_at: string;
}

export default function ContentPage() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"videos" | "topics">("videos");

  useEffect(() => {
    async function fetchData() {
      try {
        const [videosRes, topicsRes] = await Promise.all([
          fetch(`${API_URL}/api/dashboard/videos?limit=20`),
          fetch(`${API_URL}/api/dashboard/topics?limit=20`),
        ]);
        
        if (videosRes.ok) {
          const data = await videosRes.json();
          setVideos(data.videos || []);
        }
        if (topicsRes.ok) {
          const data = await topicsRes.json();
          setTopics(data.topics || []);
        }
      } catch (error) {
        console.error("Failed to fetch content:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const contentTypeColors: Record<string, string> = {
    sales_tip: "bg-emerald-500/20 text-emerald-400",
    ai_news: "bg-blue-500/20 text-blue-400",
    hot_take: "bg-orange-500/20 text-orange-400",
    product_showcase: "bg-purple-500/20 text-purple-400",
  };

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Content Library</h1>
        <p className="text-slate-400 mt-1">
          All generated videos and topics
        </p>
      </header>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-slate-700">
        <button
          onClick={() => setActiveTab("videos")}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
            activeTab === "videos"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Video className="w-4 h-4" />
          Videos ({videos.length})
        </button>
        <button
          onClick={() => setActiveTab("topics")}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
            activeTab === "topics"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Lightbulb className="w-4 h-4" />
          Topics ({topics.length})
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-40 bg-slate-700 rounded-lg mb-4" />
              <div className="h-4 w-3/4 bg-slate-700 rounded mb-2" />
              <div className="h-3 w-1/2 bg-slate-700 rounded" />
            </div>
          ))}
        </div>
      ) : activeTab === "videos" ? (
        videos.length === 0 ? (
          <div className="card py-16 text-center">
            <Video className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-300 mb-2">No videos yet</h3>
            <p className="text-slate-500">Run the pipeline to generate your first video</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((video) => (
              <div key={video.id} className="card overflow-hidden">
                <div className="relative h-40 bg-slate-800 -mx-4 -mt-4 mb-4">
                  {video.thumbnail_url ? (
                    <Image
                      src={video.thumbnail_url}
                      alt={video.title}
                      fill
                      className="object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <Video className="w-12 h-12 text-slate-600" />
                    </div>
                  )}
                  <span className="absolute bottom-2 right-2 bg-red-600 text-white text-xs px-1.5 py-0.5 rounded">
                    SHORT
                  </span>
                </div>
                <h3 className="font-medium text-slate-200 truncate mb-2">{video.title}</h3>
                <div className="flex items-center gap-4 text-sm text-slate-500">
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {video.views}
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3" />
                    {video.likes}
                  </span>
                  {video.youtube_url && (
                    <a
                      href={video.youtube_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-auto text-brand-400 hover:text-brand-300"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      ) : topics.length === 0 ? (
        <div className="card py-16 text-center">
          <Lightbulb className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">No topics yet</h3>
          <p className="text-slate-500">Topics will appear after running the pipeline</p>
        </div>
      ) : (
        <div className="space-y-3">
          {topics.map((topic) => (
            <div key={topic.id} className="card flex items-center gap-4">
              <div className="p-2 bg-slate-700/50 rounded-lg">
                <Lightbulb className="w-5 h-5 text-amber-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-slate-200 truncate">{topic.title}</h3>
                <p className="text-sm text-slate-500 truncate">{topic.hook}</p>
              </div>
              <span className={`px-2 py-1 text-xs rounded-full ${contentTypeColors[topic.content_type] || "bg-slate-700 text-slate-400"}`}>
                {topic.content_type?.replace("_", " ")}
              </span>
              <span className={`px-2 py-1 text-xs rounded-full ${
                topic.status === "used" 
                  ? "bg-emerald-500/20 text-emerald-400" 
                  : "bg-slate-700 text-slate-400"
              }`}>
                {topic.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

