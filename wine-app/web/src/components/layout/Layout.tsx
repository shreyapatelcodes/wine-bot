/**
 * Main app layout component
 */

import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { WineListsSidebar } from './WineListsSidebar';
import { ChatProvider } from '../../context/ChatContext';

export function Layout() {
  return (
    <ChatProvider>
      <div className="min-h-screen bg-cream flex">
        {/* Persistent left rail with user lists */}
        <WineListsSidebar />

        {/* Main content area */}
        <div className="flex-1 min-w-0">
          {/* User menu in top-right */}
          <Sidebar />
          <main>
            <Outlet />
          </main>
        </div>
      </div>
    </ChatProvider>
  );
}
