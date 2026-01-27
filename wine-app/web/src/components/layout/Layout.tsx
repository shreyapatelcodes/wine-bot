/**
 * Main app layout component
 */

import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="min-h-screen bg-cream">
      <Sidebar />
      <main className="pt-16">
        <Outlet />
      </main>
    </div>
  );
}
