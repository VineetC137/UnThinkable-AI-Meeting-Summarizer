import React from 'react';
import { useUser } from '@/stores/auth';

const ProfilePage: React.FC = () => {
  const user = useUser();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Profile
        </h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Manage your account information and preferences.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Account Information
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Email</label>
            <div className="mt-1 text-gray-900 dark:text-white">
              {user?.email}
            </div>
          </div>
          
          <div>
            <label className="label">Username</label>
            <div className="mt-1 text-gray-900 dark:text-white">
              {user?.username}
            </div>
          </div>
          
          <div>
            <label className="label">Full Name</label>
            <div className="mt-1 text-gray-900 dark:text-white">
              {user?.full_name || 'Not provided'}
            </div>
          </div>
          
          <div>
            <label className="label">Role</label>
            <div className="mt-1">
              <span className="badge-default capitalize">
                {user?.role}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;