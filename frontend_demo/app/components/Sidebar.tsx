import { Activity, FileText, Settings, BarChart3 } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export function Sidebar() {
  const location = useLocation();
  
  const navItems = [
    { icon: Activity, label: 'Dashboard', path: '/' },
    { icon: FileText, label: 'Transcripts', path: '/transcripts' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  return (
    <aside className="w-64 border-r border-[#27272a] bg-black flex flex-col">
      <div className="p-6 border-b border-[#27272a]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center relative">
            <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C9.5 2 7.5 3.5 7.5 5.5C7.5 6.5 8 7.5 9 8.5C8 9 7 9.5 6.5 10.5C6 11.5 6 12.5 6.5 13.5C7 14.5 8 15 9 15.5C8.5 16 8 16.5 8 17.5C8 19 9 20 10.5 20.5C11 20.8 11.5 21 12 21C12.5 21 13 20.8 13.5 20.5C15 20 16 19 16 17.5C16 16.5 15.5 16 15 15.5C16 15 17 14.5 17.5 13.5C18 12.5 18 11.5 17.5 10.5C17 9.5 16 9 15 8.5C16 7.5 16.5 6.5 16.5 5.5C16.5 3.5 14.5 2 12 2ZM10 4.5C10 4.2 10.2 4 10.5 4H13.5C13.8 4 14 4.2 14 4.5C14 5.5 13.5 6 12.5 6.5C12.3 6.6 12.2 6.6 12 6.6C11.8 6.6 11.7 6.6 11.5 6.5C10.5 6 10 5.5 10 4.5Z"/>
            </svg>
          </div>
          <span className="text-[16px] font-semibold text-white">Wisp</span>
        </div>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <li key={item.label}>
                <Link
                  to={item.path}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-zinc-900 text-white'
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-[14px] font-medium">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-[#27272a]">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
            <span className="text-xs font-semibold text-white">YL</span>
          </div>
          <div className="flex-1">
            <div className="text-[14px] font-medium text-white">Yao Liew</div>
            <div className="text-xs text-zinc-500">zyliew7@gmail.com</div>
          </div>
        </div>
      </div>
    </aside>
  );
}