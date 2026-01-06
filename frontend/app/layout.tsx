import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata: Metadata = {
  title: "DealMotion Marketing Engine",
  description: "Automated YouTube content generation dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="antialiased min-h-screen">
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <aside className="w-64 bg-surface border-r border-slate-800 p-4 flex flex-col">
            <div className="mb-8">
              <h1 className="text-xl font-bold text-brand-400">🎬 DealMotion</h1>
              <p className="text-xs text-slate-500 mt-1">Marketing Engine</p>
            </div>
            
            <nav className="flex-1 space-y-1">
              <NavLink href="/" icon="📊" label="Dashboard" />
              <NavLink href="/pipeline" icon="⚡" label="Pipeline" />
              <NavLink href="/content" icon="📝" label="Content" />
              <NavLink href="/analytics" icon="📈" label="Analytics" />
              <NavLink href="/settings" icon="⚙️" label="Settings" />
            </nav>

            <div className="pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="status-dot success"></span>
                <span>System healthy</span>
              </div>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ href, icon, label }: { href: string; icon: string; label: string }) {
  return (
    <a
      href={href}
      className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-surface-light transition-colors"
    >
      <span>{icon}</span>
      <span className="text-sm font-medium">{label}</span>
    </a>
  );
}

