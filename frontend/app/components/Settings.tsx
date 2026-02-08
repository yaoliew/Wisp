import { useState } from 'react';
import { Settings as SettingsIcon, CreditCard, Shield, Database, Eye } from 'lucide-react';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

export function Settings() {
  // State for all settings (non-functional, just for visuals)
  const [sessionManagement, setSessionManagement] = useState(true);
  const [digestMode, setDigestMode] = useState('weekly');
  const [creditCardBalance, setCreditCardBalance] = useState(32.67);
  const [autoTopoff, setAutoTopoff] = useState(false);
  const [dataRetention, setDataRetention] = useState('7 days');
  const [autoMasking, setAutoMasking] = useState(true);

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-[24px] font-semibold text-white">Settings</h1>
        <p className="text-[13px] text-zinc-500 mt-1">Manage your account preferences and security settings</p>
      </div>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Session Management */}
        <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="px-6 py-5">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-1">
                <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                  <SettingsIcon className="w-5 h-5 text-zinc-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-[16px] font-semibold text-white mb-1">Session Management</h3>
                  <p className="text-[13px] text-zinc-400">
                    Automatically manage and clean up active sessions
                  </p>
                </div>
              </div>
              <Switch
                checked={sessionManagement}
                onCheckedChange={setSessionManagement}
                className="mt-1"
              />
            </div>
          </div>
        </div>

        {/* Digest Mode */}
        <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="px-6 py-5">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                <Database className="w-5 h-5 text-zinc-400" />
              </div>
              <div className="flex-1">
                <Label htmlFor="digest-mode" className="text-[16px] font-semibold text-white mb-1 block">
                  Digest Mode
                </Label>
                <p className="text-[13px] text-zinc-400 mb-3">
                  Choose how often you receive summary reports
                </p>
                <Select value={digestMode} onValueChange={setDigestMode}>
                  <SelectTrigger id="digest-mode" className="w-[200px] bg-zinc-900 border-[#27272a] text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-[#27272a] text-white">
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>

        {/* Credit Card Balance */}
        <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="px-6 py-5">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                <CreditCard className="w-5 h-5 text-zinc-400" />
              </div>
              <div className="flex-1 space-y-4">
                <div>
                  <h3 className="text-[16px] font-semibold text-white mb-1">Credit Card Balance</h3>
                  <p className="text-[13px] text-zinc-400 mb-3">
                    Current balance and auto-topoff settings
                  </p>
                  <div className="flex items-center gap-3">
                    <div className="text-[32px] font-semibold text-white">
                      ${creditCardBalance.toFixed(2)}
                    </div>
                    <div className="text-[13px] text-zinc-500">USD</div>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-[#27272a]">
                  <div>
                    <Label htmlFor="auto-topoff" className="text-[14px] font-medium text-white">
                      Auto-Topoff
                    </Label>
                    <p className="text-[12px] text-zinc-500 mt-0.5">
                      Automatically add funds when balance falls below $3
                    </p>
                  </div>
                  <Switch
                    id="auto-topoff"
                    checked={autoTopoff}
                    onCheckedChange={setAutoTopoff}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Data Retention Policy */}
        <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="px-6 py-5">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                <Database className="w-5 h-5 text-zinc-400" />
              </div>
              <div className="flex-1">
                <Label htmlFor="data-retention" className="text-[16px] font-semibold text-white mb-1 block">
                  Data Retention Policy
                </Label>
                <p className="text-[13px] text-zinc-400 mb-3">
                  Set transcripts to delete after a specified period
                </p>
                <Select value={dataRetention} onValueChange={setDataRetention}>
                  <SelectTrigger id="data-retention" className="w-[200px] bg-zinc-900 border-[#27272a] text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-[#27272a] text-white">
                    <SelectItem value="24 hours">24 hours</SelectItem>
                    <SelectItem value="7 days">7 days</SelectItem>
                    <SelectItem value="30 days">30 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>

        {/* Auto-Masking */}
        <div className="bg-[#09090b] rounded-lg border border-[#27272a] relative overflow-hidden">
          <div className="absolute inset-0 border border-white/[0.02] rounded-lg pointer-events-none" />
          <div className="px-6 py-5">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-1">
                <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-zinc-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-[16px] font-semibold text-white mb-1">Auto-Masking</h3>
                  <p className="text-[13px] text-zinc-400 mb-2">
                    Automatically redact sensitive information from transcripts before saving
                  </p>
                  <div className="flex flex-wrap gap-2 mt-3">
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800/50 border border-[#27272a]">
                      <Eye className="w-3 h-3 text-zinc-400" />
                      <span className="text-[12px] text-zinc-400">Social Security Numbers</span>
                    </div>
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800/50 border border-[#27272a]">
                      <CreditCard className="w-3 h-3 text-zinc-400" />
                      <span className="text-[12px] text-zinc-400">Credit Cards</span>
                    </div>
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800/50 border border-[#27272a]">
                      <Database className="w-3 h-3 text-zinc-400" />
                      <span className="text-[12px] text-zinc-400">Addresses</span>
                    </div>
                  </div>
                </div>
              </div>
              <Switch
                checked={autoMasking}
                onCheckedChange={setAutoMasking}
                className="mt-1"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
