/**
 * Main app layout component
 */

import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="min-h-screen bg-cream flex">
      <Sidebar />
      <main className="flex-1 md:ml-20 pb-20 md:pb-0">
        <Outlet />
      </main>
    </div>
  );
}
