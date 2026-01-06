"use client";

interface ContentType {
  type: string;
  label: string;
  percentage: number;
  color: string;
  count: number;
}

export function ContentMix() {
  // TODO: Fetch real data from API/settings
  const contentTypes: ContentType[] = [
    { type: "sales_tip", label: "Sales Tips", percentage: 40, color: "bg-emerald-500", count: 0 },
    { type: "ai_news", label: "AI News", percentage: 25, color: "bg-blue-500", count: 0 },
    { type: "hot_take", label: "Hot Takes", percentage: 20, color: "bg-orange-500", count: 0 },
    { type: "product", label: "Product", percentage: 15, color: "bg-purple-500", count: 0 },
  ];

  return (
    <div className="card h-full">
      <div className="card-header">
        <h2 className="card-title">Content Mix</h2>
        <span className="text-xs text-slate-500">Target %</span>
      </div>

      <div className="space-y-4">
        {contentTypes.map((type) => (
          <div key={type.type}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-300">{type.label}</span>
              <span className="text-sm text-slate-500">
                {type.count} videos ({type.percentage}%)
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

      <div className="mt-6 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-500">
          Adjust mix in Settings → Content Strategy
        </p>
      </div>
    </div>
  );
}

