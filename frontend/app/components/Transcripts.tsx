import { FileText, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import { Fragment, useState, useEffect } from 'react';
import { fetchTranscriptMetrics, fetchCalls, TranscriptMetricsResponse, DBCall } from '../lib/api';
import { transformCalls, CallLog } from '../lib/transformers';
import { Button } from './ui/button';

export function Transcripts() {
  const [metrics, setMetrics] = useState<TranscriptMetricsResponse | null>(null);
  const [transcripts, setTranscripts] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTranscripts, setExpandedTranscripts] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        
        // Load metrics and transcripts in parallel
        const [metricsData, callsData] = await Promise.all([
          fetchTranscriptMetrics(),
          fetchCalls()
        ]);
        
        setMetrics(metricsData);
        
        // Filter to only calls with transcripts and transform
        const callsWithTranscripts = callsData.calls.filter(
          (call: DBCall) => call.transcript && call.transcript.trim() !== ''
        );
        const transformed = transformCalls(callsWithTranscripts);
        setTranscripts(transformed);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transcripts');
        console.error('Error loading transcripts:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const getVerdictBadge = (verdict: CallLog['verdict']) => {
    if (verdict === 'PHISHING') {
      return (
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-950/50 border border-red-800/50">
          <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <span className="text-[12px] font-semibold text-red-400">PHISHING</span>
        </div>
      );
    }
    
    // Default to SAFE for all non-PHISHING verdicts
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-emerald-800/50">
        <span className="text-[12px] font-semibold text-emerald-500">SAFE</span>
      </div>
    );
  };

  const toggleTranscript = (logId: string) => {
    setExpandedTranscripts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };

  const getWordCount = (transcript: CallLog['transcript']): number => {
    if (!transcript || transcript.length === 0) return 0;
    return transcript.reduce((total, line) => {
      return total + line.text.split(/\s+/).filter(word => word.length > 0).length;
    }, 0);
  };

  return (
    <div className="p-8 space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-2 gap-6">
        {/* Average Word Count Card */}
        <div className="bg-[#09090b] rounded-lg p-6 border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-zinc-400" />
              <div className="text-[13px] font-medium text-zinc-400">Average Length of Call</div>
            </div>
            {loading && (
              <div className="text-zinc-500 text-sm">Loading...</div>
            )}
            {error && (
              <div className="text-red-400 text-sm">Error loading metrics</div>
            )}
            {!loading && !error && metrics && (
              <div>
                <div className="text-[32px] font-semibold text-white leading-none">
                  {metrics.average_word_count.toLocaleString()}
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-xs text-zinc-500">words per call</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Total Transcripts Card */}
        <div className="bg-[#09090b] rounded-lg p-6 border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-zinc-400" />
              <div className="text-[13px] font-medium text-zinc-400">Stored Transcripts</div>
            </div>
            {loading && (
              <div className="text-zinc-500 text-sm">Loading...</div>
            )}
            {error && (
              <div className="text-red-400 text-sm">Error loading metrics</div>
            )}
            {!loading && !error && metrics && (
              <div>
                <div className="text-[32px] font-semibold text-white leading-none">
                  {metrics.total_transcripts.toLocaleString()}
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-xs text-zinc-500">transcripts available</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Transcripts Table */}
      <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
        <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
        
        <div className="px-6 py-4 border-b border-[#27272a]">
          <h2 className="text-[18px] font-semibold text-white">All Transcripts</h2>
          <p className="text-[13px] text-zinc-500 mt-1">Complete call transcripts with AI analysis</p>
        </div>

        {loading && (
          <div className="px-6 py-12 text-center">
            <div className="text-zinc-400 text-sm">Loading transcripts...</div>
          </div>
        )}

        {error && (
          <div className="px-6 py-12 text-center">
            <div className="text-red-400 text-sm mb-2">Error loading transcripts: {error}</div>
            <Button
              variant="ghost"
              className="text-zinc-400 hover:text-white"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        )}

        {!loading && !error && transcripts.length === 0 && (
          <div className="px-6 py-12 text-center">
            <div className="text-zinc-400 text-sm">No transcripts found</div>
          </div>
        )}

        {!loading && !error && transcripts.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-[#27272a]">
                <tr>
                  <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Timestamp</th>
                  <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Caller</th>
                  <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Word Count</th>
                  <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">AI Summary</th>
                  <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272a]">
                {transcripts.map((log) => {
                  const wordCount = getWordCount(log.transcript);
                  const isExpanded = expandedTranscripts.has(log.id);
                  return (
                    <Fragment key={log.id}>
                      <tr 
                        className="hover:bg-zinc-900/30 transition-colors cursor-pointer"
                        onClick={() => toggleTranscript(log.id)}
                      >
                        <td className="px-6 py-4">
                          <span className="text-[14px] text-zinc-300">{log.timestamp}</span>
                        </td>
                        <td className="px-6 py-4">
                          <div>
                            <div className="text-[14px] font-medium text-white">{log.callerName}</div>
                            <div className="text-[13px] text-zinc-500">{log.callerPhone}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-[14px] text-zinc-400">{wordCount.toLocaleString()} words</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-[14px] text-zinc-400">{log.aiSummary}</span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {getVerdictBadge(log.verdict)}
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4 text-zinc-400" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-zinc-400" />
                            )}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr key={`${log.id}-expanded`} className="bg-zinc-950/50">
                          <td colSpan={5} className="px-6 py-6">
                            <div className="space-y-3">
                              <div className="flex items-center gap-3 pb-3 border-b border-[#27272a]">
                                <div>
                                  <div className="text-[14px] font-medium text-white">{log.callerName}</div>
                                  <div className="text-[13px] text-zinc-500">{log.callerPhone}</div>
                                </div>
                                <div className="ml-auto">
                                  {getVerdictBadge(log.verdict)}
                                </div>
                              </div>
                              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                                {log.transcript.map((line, index) => (
                                  <div key={index} className="flex gap-3">
                                    <span className="text-[12px] text-zinc-500 min-w-[40px] mt-1">{line.time}</span>
                                    <div className="flex-1">
                                      <div className={`rounded-lg px-4 py-3 ${
                                        line.speaker === 'AI Assistant' 
                                          ? 'bg-zinc-900 border border-[#27272a]' 
                                          : 'bg-zinc-800/50'
                                      }`}>
                                        <div className="text-[13px] font-semibold text-zinc-300 mb-1">
                                          {line.speaker}
                                        </div>
                                        <div className="text-[14px] text-zinc-400">
                                          {line.text}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
