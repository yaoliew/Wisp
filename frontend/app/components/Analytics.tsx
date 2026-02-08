import { useState, useEffect } from 'react';
import { fetchAnalytics, AnalyticsResponse } from '../lib/api';
import { CallsBarChart } from './CallsBarChart';
import { BlockedCallsBarChart } from './BlockedCallsBarChart';
import { ScamSafePieChart } from './ScamSafePieChart';

type Period = 'daily' | 'weekly' | 'monthly';

export function Analytics() {
  const [period, setPeriod] = useState<Period>('daily');
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchAnalytics(period);
        setAnalytics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
        console.error('Error loading analytics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [period]);

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header with Period Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[24px] font-semibold text-white">Analytics</h1>
          <p className="text-[13px] text-zinc-500 mt-1">Call analytics and insights</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPeriod('daily')}
            className={`px-4 py-2 rounded-md text-[13px] font-medium transition-colors ${
              period === 'daily'
                ? 'bg-zinc-900 text-white border border-[#27272a]'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
            }`}
          >
            Daily
          </button>
          <button
            onClick={() => setPeriod('weekly')}
            className={`px-4 py-2 rounded-md text-[13px] font-medium transition-colors ${
              period === 'weekly'
                ? 'bg-zinc-900 text-white border border-[#27272a]'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
            }`}
          >
            Weekly
          </button>
          <button
            onClick={() => setPeriod('monthly')}
            className={`px-4 py-2 rounded-md text-[13px] font-medium transition-colors ${
              period === 'monthly'
                ? 'bg-zinc-900 text-white border border-[#27272a]'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
            }`}
          >
            Monthly
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="text-zinc-400 text-sm">Loading analytics...</div>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <div className="text-red-400 text-sm mb-2">Error loading analytics: {error}</div>
        </div>
      )}

      {!loading && !error && analytics && (
        <div className="space-y-6">
          {/* 1. Calls per period bar chart */}
          <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
            <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
            <div className="px-6 py-4 border-b border-[#27272a]">
              <h2 className="text-[18px] font-semibold text-white">Calls Received</h2>
              <p className="text-[13px] text-zinc-500 mt-1">Total number of calls by {period} period</p>
            </div>
            <div className="p-6">
              {analytics.calls_by_period.length > 0 ? (
                <CallsBarChart data={analytics.calls_by_period} />
              ) : (
                <div className="text-center py-12 text-zinc-500 text-sm">No data available</div>
              )}
            </div>
          </div>

          {/* 2. Blocked calls per period bar chart */}
          <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
            <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
            <div className="px-6 py-4 border-b border-[#27272a]">
              <h2 className="text-[18px] font-semibold text-white">Incoming Calls Blocked</h2>
              <p className="text-[13px] text-zinc-500 mt-1">Number of blocked calls by {period} period</p>
            </div>
            <div className="p-6">
              {analytics.blocked_by_period.length > 0 ? (
                <BlockedCallsBarChart data={analytics.blocked_by_period} />
              ) : (
                <div className="text-center py-12 text-zinc-500 text-sm">No data available</div>
              )}
            </div>
          </div>

          {/* 3. Scam-to-safe ratio pie chart */}
          <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
            <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
            <div className="px-6 py-4 border-b border-[#27272a]">
              <h2 className="text-[18px] font-semibold text-white">Scam-to-Safe Ratio</h2>
              <p className="text-[13px] text-zinc-500 mt-1">Distribution of call verdicts</p>
            </div>
            <div className="p-6">
              {analytics.scam_safe_ratio.scam + analytics.scam_safe_ratio.safe > 0 ? (
                <ScamSafePieChart data={analytics.scam_safe_ratio} />
              ) : (
                <div className="text-center py-12 text-zinc-500 text-sm">No data available</div>
              )}
            </div>
          </div>

          {/* 4. Average call duration */}
          <div className="bg-[#09090b] rounded-lg p-6 border border-[#27272a] relative overflow-hidden">
            <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
            <div className="space-y-3">
              <div className="text-[13px] font-medium text-zinc-400">Average Call Duration</div>
              <div>
                <div className="text-[32px] font-semibold text-white leading-none">
                  {analytics.avg_call_duration > 0 ? formatDuration(analytics.avg_call_duration) : 'N/A'}
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-xs text-zinc-500">Average time per call</span>
                </div>
              </div>
            </div>
          </div>

          {/* 5. Top scam categories */}
          <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
            <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
            <div className="px-6 py-4 border-b border-[#27272a]">
              <h2 className="text-[18px] font-semibold text-white">Top Scam Categories</h2>
              <p className="text-[13px] text-zinc-500 mt-1">Most common scam types detected</p>
            </div>
            <div className="p-6">
              {analytics.top_scam_categories.length > 0 ? (
                <div className="space-y-3">
                  {analytics.top_scam_categories.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-md bg-red-950/50 border border-red-800/50 flex items-center justify-center">
                          <span className="text-[12px] font-semibold text-red-400">{index + 1}</span>
                        </div>
                        <span className="text-[14px] font-medium text-white">{item.category}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-zinc-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-red-500"
                            style={{
                              width: `${(item.count / analytics.top_scam_categories[0].count) * 100}%`
                            }}
                          />
                        </div>
                        <span className="text-[14px] font-semibold text-zinc-300 w-12 text-right">
                          {item.count}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-zinc-500 text-sm">No scam categories available</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
