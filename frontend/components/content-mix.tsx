"use client";

import { useEffect, useState } from "react";
import { getContentMix } from "@/lib/api";

interface ContentType {
  type: string;
  label: string;
  targetPercentage: number;
  color: string;
  count: number;
}

export function ContentMix() {
  const [contentMix, setContentMix] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchContentMix() {
      try {
        const data = await getContentMix();
        setContentMix(data.content_mix || {});
      } catch (error) {
        console.error("Failed to fetch content mix:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchContentMix();
  }, []);

  const total = Object.values(contentMix).reduce((sum, count) => sum + count, 0);

  const contentTypes: ContentType[] = [
    { 
      type: "sales_tip", 
      label: "Sales Tips", 
      targetPercentage: 40, 
      color: "bg-emerald-500", 
      count: contentMix.sales_tip || 0 
    },
    { 
      type: "ai_news", 
      label: "AI News", 
      targetPercentage: 25, 
      color: "bg-blue-500", 
      count: contentMix.ai_news || 0 
    },
    { 
      type: "hot_take", 
      label: "Hot Takes", 
      targetPercentage: 20, 
      color: "bg-orange-500", 
      count: contentMix.hot_take || 0 
    },
    { 
      type: "product_showcase", 
      label: "Product", 
      targetPercentage: 15, 
      color: "bg-purple-500", 
      count: contentMix.product_showcase || 0 
    },
  ];

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
      ) : (
        <div className="space-y-4">
          {contentTypes.map((type) => {
            const actualPercentage = total > 0 
              ? Math.round((type.count / total) * 100) 
              : 0;
            
            return (
              <div key={type.type}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-300">{type.label}</span>
                  <span className="text-sm text-slate-500">
                    {type.count} ({actualPercentage}%)
                  </span>
                </div>
                <div className="h-2 bg-surface rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${type.color} transition-all duration-500`}
                    style={{ width: `${actualPercentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-500">
          Target: 40% sales tips, 25% AI news, 20% hot takes, 15% product
        </p>
      </div>
    </div>
  );
}
