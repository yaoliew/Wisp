import { Zap } from 'lucide-react';
import { Button } from './ui/button';
import { useState, useEffect } from 'react';
import { fetchActiveCalls } from '../lib/api';
import { formatPhoneNumber } from '../lib/transformers';

export function Header() {
  const [activeCallCount, setActiveCallCount] = useState(0);
  const [activePhoneNumber, setActivePhoneNumber] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadActiveCalls() {
      try {
        setLoading(true);
        const response = await fetchActiveCalls();
        setActiveCallCount(response.count);
        if (response.calls.length > 0) {
          // Get the first active call's phone number
          const firstCall = response.calls[0];
          setActivePhoneNumber(firstCall.to_number || firstCall.from_number || null);
        } else {
          setActivePhoneNumber(null);
        }
      } catch (err) {
        console.error('Error loading active calls:', err);
        setActivePhoneNumber(null);
      } finally {
        setLoading(false);
      }
    }
    
    loadActiveCalls();
    // Refresh every 5 seconds to show live updates
    const interval = setInterval(loadActiveCalls, 5000);
    return () => clearInterval(interval);
  }, []);

  const displayPhone = activePhoneNumber ? formatPhoneNumber(activePhoneNumber) : null;
  const hasActiveCalls = activeCallCount > 0;

  return (
    <header className="border-b border-[#27272a] bg-black px-8 py-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-[24px] font-semibold text-white">Wisp</h1>
          {!loading && (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
              hasActiveCalls 
                ? 'bg-emerald-950/50 border-emerald-800/50' 
                : 'bg-zinc-900/50 border-zinc-800/50'
            }`}>
              {hasActiveCalls && (
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              )}
              <span className={`text-[13px] font-medium ${
                hasActiveCalls ? 'text-emerald-400' : 'text-zinc-500'
              }`}>
                {hasActiveCalls 
                  ? `Live: Protecting ${displayPhone || 'Active Call'}`
                  : 'No active calls'
                }
              </span>
            </div>
          )}
        </div>
        
        <Button className="bg-white text-black hover:bg-zinc-200 rounded-md px-4 py-2 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          <span className="text-[14px] font-medium">Quick Actions</span>
        </Button>
      </div>
    </header>
  );
}