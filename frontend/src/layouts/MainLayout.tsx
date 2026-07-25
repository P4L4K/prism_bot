import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { Library, Settings } from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { currentView, setCurrentView } = useAppStore();

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[var(--color-background)] font-handwritten relative">
      {/* Titlebar for Window Dragging */}
      <div className="h-10 flex items-center justify-between px-4 drag-region z-50">
        <div className="text-[var(--color-text-sec)] text-sm font-semibold tracking-widest uppercase opacity-70">
          PRISM Storybook
        </div>
        <div className="flex space-x-2 no-drag">
           <button className="w-3 h-3 rounded-full bg-yellow-400 hover:bg-yellow-500" onClick={() => window.electron?.window.minimize()}></button>
           <button className="w-3 h-3 rounded-full bg-green-400 hover:bg-green-500" onClick={() => window.electron?.window.maximize()}></button>
           <button className="w-3 h-3 rounded-full bg-red-400 hover:bg-red-500" onClick={() => window.electron?.window.close()}></button>
        </div>
      </div>
      
      {/* Floating Navigation Controls */}
      <div className="absolute top-12 left-4 z-50 flex gap-2 no-drag">
        {currentView !== 'history' && (
          <button 
            onClick={() => setCurrentView('history')}
            className="p-3 rounded-full bg-white/80 backdrop-blur-md shadow-md text-[var(--color-text-pri)] hover:bg-[var(--color-accent-soft)] hover:scale-110 transition-all border border-[var(--color-border-card)]"
            title="Return to Bookshelf"
          >
            <Library size={20} />
          </button>
        )}
        {currentView !== 'settings' && (
          <button 
            onClick={() => setCurrentView('settings')}
            className="p-3 rounded-full bg-white/80 backdrop-blur-md shadow-md text-[var(--color-text-pri)] hover:bg-[var(--color-accent-soft)] hover:scale-110 transition-all border border-[var(--color-border-card)]"
            title="Settings"
          >
            <Settings size={20} />
          </button>
        )}
      </div>
      
      {/* Page Content */}
      <main className="flex-1 overflow-hidden relative no-drag">
        {children}
      </main>
    </div>
  );
};
