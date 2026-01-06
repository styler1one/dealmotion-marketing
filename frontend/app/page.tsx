import { PipelineStatus } from "@/components/pipeline-status";
import { RecentVideos } from "@/components/recent-videos";
import { QuickStats } from "@/components/quick-stats";
import { ContentMix } from "@/components/content-mix";

export default function Dashboard() {
  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Overview of your automated content pipeline
        </p>
      </header>

      {/* Quick Stats */}
      <section className="mb-8">
        <QuickStats />
      </section>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Status - Takes 2 columns */}
        <div className="lg:col-span-2">
          <PipelineStatus />
        </div>

        {/* Content Mix */}
        <div>
          <ContentMix />
        </div>
      </div>

      {/* Recent Videos */}
      <section className="mt-8">
        <RecentVideos />
      </section>
    </div>
  );
}

