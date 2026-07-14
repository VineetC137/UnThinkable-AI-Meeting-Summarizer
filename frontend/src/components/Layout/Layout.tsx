import React from 'react';
import { Outlet } from 'react-router-dom';
import { clsx } from 'clsx';
import Sidebar from './Sidebar';
import Header from './Header';
import { useSidebarOpen } from '@/stores/ui';

const Layout: React.FC = () => {
  const sidebarOpen = useSidebarOpen();

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className={clsx(
        'flex-1 flex flex-col overflow-hidden transition-all duration-300',
        sidebarOpen ? 'ml-64' : 'ml-16'
      )}>
        {/* Header */}
        <Header />

        {/* Page content */}
        <main className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;