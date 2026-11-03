import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, Sparkles, Database } from 'lucide-react';
import { Badge } from './Badge';

interface TopBarProps {
  onMenuClick: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onMenuClick }) => {
  const location = useLocation();

  const getBreadcrumb = (path: string) => {
    if (path === '/') return 'Dashboard';
    if (path.startsWith('/leads/')) return 'Lead intelligence';
    if (path === '/leads') return 'Leads & pipeline';
    if (path === '/agent-runs') return 'Agent activity';
    if (path === '/follow-ups') return 'Follow-up center';
    if (path === '/knowledge') return 'Knowledge base';
    if (path === '/evaluation') return 'Model evaluation';
    if (path === '/settings') return 'Settings';
    return 'NexusFlow';
  };

  return (
    <header className="sticky top-0 z-20 flex min-h-[68px] items-center justify-between border-b border-[#e7e9f4]/90 bg-white/85 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          aria-label="Open navigation menu"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-[#536080] transition-colors hover:bg-[#f0f1fb] hover:text-[#373e8e] lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.13em] text-[#929bb4]">NexusFlow workspace</p>
          <h2 className="truncate text-sm font-semibold capitalize tracking-tight text-[#202b4d]">
            {getBreadcrumb(location.pathname)}
          </h2>
        </div>
      </div>

      <div className="ml-3 flex shrink-0 items-center gap-2 sm:gap-3">
        <Badge variant="primary" size="sm" className="hidden items-center gap-1.5 sm:inline-flex">
          <Sparkles className="w-3.5 h-3.5" />
          <span>LLM: Deterministic Demo Mode</span>
        </Badge>

        <Badge variant="success" size="sm" className="inline-flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5" />
          <span className="hidden md:inline">SQLite WAL Connected</span>
          <span className="md:hidden">Connected</span>
        </Badge>
      </div>
    </header>
  );
};
