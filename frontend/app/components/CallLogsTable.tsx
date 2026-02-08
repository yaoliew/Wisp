import { Eye, MoreVertical } from 'lucide-react';
import { Button } from './ui/button';
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { fetchCalls } from '../lib/api';
import { transformCalls, CallLog } from '../lib/transformers';

export function CallLogsTable() {
  const [callLogs, setCallLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);

  useEffect(() => {
    async function loadCalls() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchCalls({ limit: 50 });
        const transformed = transformCalls(response.calls);
        setCallLogs(transformed);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load calls');
        console.error('Error loading calls:', err);
      } finally {
        setLoading(false);
      }
    }
    loadCalls();
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
    
    if (verdict === 'SAFE') {
      return (
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-emerald-800/50">
          <span className="text-[12px] font-semibold text-emerald-500">SAFE</span>
        </div>
      );
    }
    
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-950/30 border border-amber-800/50">
        <span className="text-[12px] font-semibold text-amber-500">SUSPICIOUS</span>
      </div>
    );
  };

  const handleViewTranscript = (log: CallLog) => {
    setSelectedLog(log);
    setOpen(true);
  };

  return (
    <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
      <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
      
      <div className="px-6 py-4 border-b border-[#27272a]">
        <h2 className="text-[18px] font-semibold text-white">Recent Call Logs</h2>
        <p className="text-[13px] text-zinc-500 mt-1">AI-analyzed call screening results</p>
      </div>

      {loading && (
        <div className="px-6 py-12 text-center">
          <div className="text-zinc-400 text-sm">Loading calls...</div>
        </div>
      )}

      {error && (
        <div className="px-6 py-12 text-center">
          <div className="text-red-400 text-sm mb-2">Error loading calls: {error}</div>
          <Button
            variant="ghost"
            className="text-zinc-400 hover:text-white"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      )}

      {!loading && !error && callLogs.length === 0 && (
        <div className="px-6 py-12 text-center">
          <div className="text-zinc-400 text-sm">No calls found</div>
        </div>
      )}

      {!loading && !error && callLogs.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-[#27272a]">
              <tr>
                <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Timestamp</th>
                <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Caller</th>
                <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">AI Summary</th>
                <th className="px-6 py-3 text-left text-[13px] font-medium text-zinc-400">Verdict</th>
                <th className="px-6 py-3 text-right text-[13px] font-medium text-zinc-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#27272a]">
              {callLogs.map((log) => (
              <tr key={log.id} className="hover:bg-zinc-900/30 transition-colors">
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
                  <span className="text-[14px] text-zinc-400">{log.aiSummary}</span>
                </td>
                <td className="px-6 py-4">
                  {getVerdictBadge(log.verdict)}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="ghost"
                      className="text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md px-3 py-1.5 text-[13px] font-medium"
                      onClick={() => handleViewTranscript(log)}
                    >
                      <Eye className="w-3.5 h-3.5 mr-1.5" />
                      View Transcript
                    </Button>
                    <Button
                      variant="ghost"
                      className="text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md p-1.5"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>
                </td>
              </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl bg-[#09090b] border-[#27272a] text-white">
          <DialogHeader>
            <DialogTitle className="text-white text-[20px]">Call Transcript</DialogTitle>
            {selectedLog && (
              <div className="flex items-center gap-3 pt-2">
                <div>
                  <div className="text-[14px] font-medium text-white">{selectedLog.callerName}</div>
                  <div className="text-[13px] text-zinc-500">{selectedLog.callerPhone}</div>
                </div>
                <div className="ml-auto">
                  {getVerdictBadge(selectedLog.verdict)}
                </div>
              </div>
            )}
          </DialogHeader>
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
            {selectedLog?.transcript.map((line, index) => (
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
        </DialogContent>
      </Dialog>
    </div>
  );
}