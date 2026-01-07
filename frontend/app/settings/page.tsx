"use client";

import { useState } from "react";
import { Settings, Globe, Clock, Zap, Youtube, Save, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const [saving, setSaving] = useState(false);

  const settings = {
    general: [
      { id: "language", label: "Content Language", value: "Nederlands", type: "select", options: ["Nederlands", "English"] },
      { id: "shorts_per_day", label: "Shorts per Day", value: "1", type: "number" },
      { id: "publish_hour", label: "Publish Hour", value: "10:00", type: "time" },
      { id: "auto_publish", label: "Auto Publish", value: true, type: "toggle" },
    ],
    contentMix: [
      { id: "sales_tip", label: "Sales Tips", value: 40, color: "bg-emerald-500" },
      { id: "ai_news", label: "AI News", value: 25, color: "bg-blue-500" },
      { id: "hot_take", label: "Hot Takes", value: 20, color: "bg-orange-500" },
      { id: "product_showcase", label: "Product", value: 15, color: "bg-purple-500" },
    ],
  };

  return (
    <div className="p-8 max-w-4xl">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="text-slate-400 mt-1">
          Configure your content generation pipeline
        </p>
      </header>

      {/* General Settings */}
      <section className="card mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-brand-500/10 rounded-lg">
            <Settings className="w-5 h-5 text-brand-400" />
          </div>
          <h2 className="text-lg font-medium text-slate-200">General</h2>
        </div>

        <div className="space-y-4">
          {settings.general.map((setting) => (
            <div key={setting.id} className="flex items-center justify-between py-3 border-b border-slate-700 last:border-0">
              <div>
                <label className="text-sm font-medium text-slate-300">{setting.label}</label>
              </div>
              <div>
                {setting.type === "select" ? (
                  <select className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200">
                    {setting.options?.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : setting.type === "number" ? (
                  <input
                    type="number"
                    defaultValue={setting.value as string}
                    className="w-20 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 text-center"
                  />
                ) : setting.type === "time" ? (
                  <input
                    type="time"
                    defaultValue={setting.value as string}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  />
                ) : setting.type === "toggle" ? (
                  <button
                    className={`w-12 h-6 rounded-full transition-colors ${
                      setting.value ? "bg-brand-500" : "bg-slate-700"
                    }`}
                  >
                    <div
                      className={`w-5 h-5 bg-white rounded-full transition-transform ${
                        setting.value ? "translate-x-6" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Content Mix */}
      <section className="card mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Zap className="w-5 h-5 text-blue-400" />
          </div>
          <h2 className="text-lg font-medium text-slate-200">Content Mix</h2>
          <span className="text-xs text-slate-500 ml-auto">Target distribution</span>
        </div>

        <div className="space-y-4">
          {settings.contentMix.map((type) => (
            <div key={type.id}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-300">{type.label}</span>
                <span className="text-sm text-slate-500">{type.value}%</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${type.color} transition-all`}
                    style={{ width: `${type.value}%` }}
                  />
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  defaultValue={type.value}
                  className="w-24 accent-brand-500"
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* API Connections */}
      <section className="card mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-purple-500/10 rounded-lg">
            <Globe className="w-5 h-5 text-purple-400" />
          </div>
          <h2 className="text-lg font-medium text-slate-200">API Connections</h2>
        </div>

        <div className="space-y-3">
          {[
            { name: "Claude (Anthropic)", status: "connected", color: "emerald" },
            { name: "ElevenLabs TTS", status: "connected", color: "emerald" },
            { name: "Google Veo 2", status: "connected", color: "emerald" },
            { name: "Creatomate", status: "connected", color: "emerald" },
            { name: "YouTube API", status: "connected", color: "emerald" },
            { name: "Supabase", status: "connected", color: "emerald" },
          ].map((api) => (
            <div key={api.name} className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-300">{api.name}</span>
              <span className={`flex items-center gap-2 text-xs text-${api.color}-400`}>
                <span className={`w-2 h-2 rounded-full bg-${api.color}-500`} />
                {api.status}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        <button className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors">
          Reset to Defaults
        </button>
        <button
          onClick={() => {
            setSaving(true);
            setTimeout(() => setSaving(false), 1000);
          }}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:bg-brand-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {saving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
}

