import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Bot,
  MailCheck,
  BookOpen,
  LineChart,
  Settings as SettingsIcon,
  Zap
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onNavigate: () => void;
}

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard },
  { label: 'Leads & Pipeline', to: '/leads', icon: Users },
  { label: 'Agent Activity', to: '/agent-runs', icon: Bot },
  { label: 'Follow-Up Center', to: '/follow-ups', icon: MailCheck },
  { label: 'Knowledge Base', to: '/knowledge', icon: BookOpen },
  { label: 'Model Evaluation', to: '/evaluation', icon: LineChart },
  { label: 'Settings', to: '/settings', icon: SettingsIcon },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onNavigate }) => {
  return (
    <aside className={`fixed inset-y-0 left-0 z-40 flex h-screen w-[264px] shrink-0 flex-col border-r border-white/[0.07] bg-[#171f46] text-white shadow-[8px_0_28px_rgba(30,39,87,0.08)] transition-transform duration-200 lg:sticky lg:top-0 lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-[76px] items-center gap-3 border-b border-white/[0.08] px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-gradient-to-br from-[#6482ff] to-[#9a6bff] shadow-[0_6px_16px_rgba(112,111,255,0.28)]">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-[15px] font-semibold tracking-wide text-white">NexusFlow</h1>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.14em] text-[#aeb9e7]">AI Sales Intelligence</p>
        </div>
      </div>

      <nav aria-label="Main navigation" className="flex-1 space-y-1 overflow-y-auto px-3 py-6">
        <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#8994c4]">Workspace</p>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={onNavigate}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-xl px-3.5 py-3 text-[13px] font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-[#5369df] to-[#6256c9] text-white shadow-[0_6px_18px_rgba(74,84,186,0.32)]'
                  : 'text-[#c0c8e5] hover:bg-white/[0.07] hover:text-white'
              }`
            }
          >
            <item.icon className="h-[17px] w-[17px] shrink-0 opacity-85 transition-transform group-hover:scale-105" strokeWidth={1.8} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/[0.08] p-4">
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.05] p-3.5">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_9px_rgba(52,211,153,0.6)]" />
            <span className="text-[11px] font-semibold text-[#e0e5fb]">Local Sandbox</span>
          </div>
          <p className="mt-1.5 text-[10px] leading-4 text-[#aab4d7]">
            FastAPI + Chroma + LangGraph Engine
          </p>
        </div>
      </div>
    </aside>
  );
};
