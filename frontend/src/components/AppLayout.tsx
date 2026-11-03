import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#f5f6ff] text-[#17203d]">
      {isSidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-[#111a3b]/45 backdrop-blur-[2px] lg:hidden"
        />
      )}
      <Sidebar
        isOpen={isSidebarOpen}
        onNavigate={() => setIsSidebarOpen(false)}
      />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <TopBar onMenuClick={() => setIsSidebarOpen((open) => !open)} />
        <main className="relative flex-1 overflow-y-auto bg-[radial-gradient(ellipse_at_70%_0%,rgba(211,216,255,0.42),transparent_38%),linear-gradient(135deg,#f8f8ff_0%,#f4f6ff_52%,#f8f9ff_100%)] px-4 py-6 sm:px-6 lg:px-8">
          <div className="relative mx-auto w-full max-w-[1440px] space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
