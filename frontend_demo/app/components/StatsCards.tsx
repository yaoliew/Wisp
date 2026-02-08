import { TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { useState, useEffect } from 'react';
import { fetchStats, StatsResponse } from '../lib/api';

export function StatsCards() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stats');
        console.error('Error loading stats:', err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  // Generate sparkline data from stats (simplified - in production, you'd fetch historical data)
  const sparklineData = stats ? [
    { value: stats.blocked_last_week || 0 },
    { value: Math.max(0, (stats.blocked_this_week || 0) - 5) },
    { value: Math.max(0, (stats.blocked_this_week || 0) - 3) },
    { value: Math.max(0, (stats.blocked_this_week || 0) - 1) },
    { value: Math.max(0, (stats.blocked_this_week || 0) - 2) },
    { value: Math.max(0, (stats.blocked_this_week || 0) - 1) },
    { value: stats.blocked_this_week || 0 },
  ] : [];

  const trendPercentage = stats?.trend_percentage || 0;
  const isPositiveTrend = trendPercentage >= 0;

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Blocked This Week Card */}
      <div className="bg-[#09090b] rounded-lg p-6 border border-[#27272a] relative overflow-hidden">
        <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
        <div className="space-y-3">
          <div className="text-[13px] font-medium text-zinc-400">Blocked This Week</div>
          {loading && (
            <div className="text-zinc-500 text-sm">Loading...</div>
          )}
          {error && (
            <div className="text-red-400 text-sm">Error loading stats</div>
          )}
          {!loading && !error && stats && (
            <div className="flex items-end justify-between">
              <div>
                <div className="text-[32px] font-semibold text-white leading-none">
                  {stats.blocked_this_week}
                </div>
                <div className="flex items-center gap-1 mt-2">
                  {isPositiveTrend ? (
                    <TrendingUp className="w-3 h-3 text-emerald-500" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                  <span className={`text-xs font-medium ${isPositiveTrend ? 'text-emerald-500' : 'text-red-500'}`}>
                    {isPositiveTrend ? '+' : ''}{trendPercentage.toFixed(1)}%
                  </span>
                  <span className="text-xs text-zinc-500">vs last week</span>
                </div>
              </div>
              {sparklineData.length > 0 && (
                <div className="w-24 h-12">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={sparklineData}>
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={isPositiveTrend ? "#10b981" : "#ef4444"}
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Total Protected Card */}
      <div className="bg-[#09090b] rounded-lg p-6 border border-[#27272a] relative overflow-hidden">
        <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
        <div className="space-y-3">
          <div className="text-[13px] font-medium text-zinc-400">Total Protected</div>
          {loading && (
            <div className="text-zinc-500 text-sm">Loading...</div>
          )}
          {error && (
            <div className="text-red-400 text-sm">Error loading stats</div>
          )}
          {!loading && !error && stats && (
            <div>
              <div className="text-[32px] font-semibold text-red-500 leading-none">
                {stats.total_protected}
              </div>
              <div className="flex items-center gap-1 mt-2">
                <span className="text-xs text-zinc-500">High-risk calls prevented</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}