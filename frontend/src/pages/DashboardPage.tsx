import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  PlusIcon,
  FolderIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { APIClient } from '@/lib/api';
import { useUser } from '@/stores/auth';
import LoadingSpinner from '@/components/UI/LoadingSpinner';

const DashboardPage: React.FC = () => {
  const user = useUser();

  // Fetch recent meetings
  const { data: meetingsData, isLoading: meetingsLoading } = useQuery(
    'recent-meetings',
    () => APIClient.getMeetings({ page: 1, per_page: 5 }),
    { enabled: !!user }
  );

  // Fetch analytics
  const { data: analytics, isLoading: analyticsLoading } = useQuery(
    'meeting-analytics',
    APIClient.getMeetingAnalytics,
    { enabled: !!user }
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'pending':
      case 'transcribing':
      case 'summarizing':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome back, {user?.full_name || user?.username}!
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your meeting recordings and AI-powered summaries from your dashboard.
        </p>
      </div>

      {/* Quick stats */}
      {analyticsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Meetings
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {analytics?.total_meetings || 0}
                </p>
              </div>
              <FolderIcon className="w-8 h-8 text-primary-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Hours Processed
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {analytics?.total_duration_hours?.toFixed(1) || '0.0'}
                </p>
              </div>
              <ClockIcon className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Avg. Processing Time
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Math.round(analytics?.avg_processing_time_seconds || 0)}s
                </p>
              </div>
              <CheckCircleIcon className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Completed Today
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {analytics?.status_breakdown?.completed || 0}
                </p>
              </div>
              <CheckCircleIcon className="w-8 h-8 text-emerald-600" />
            </div>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link
            to="/upload"
            className="flex items-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors group"
          >
            <PlusIcon className="w-8 h-8 text-gray-400 group-hover:text-primary-500 dark:group-hover:text-primary-400 mr-3" />
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                Upload Meeting
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Upload a new audio recording
              </p>
            </div>
          </Link>

          <Link
            to="/meetings"
            className="flex items-center p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <FolderIcon className="w-8 h-8 text-gray-600 dark:text-gray-400 mr-3" />
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                View All Meetings
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Browse your meeting library
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent meetings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Meetings
            </h2>
            <Link
              to="/meetings"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 font-medium"
            >
              View all
            </Link>
          </div>
        </div>

        <div className="p-6">
          {meetingsLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse flex items-center space-x-4">
                  <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : meetingsData?.meetings?.length ? (
            <div className="space-y-4">
              {meetingsData.meetings.map((meeting) => (
                <Link
                  key={meeting.id}
                  to={`/meetings/${meeting.id}`}
                  className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex-shrink-0">
                    {getStatusIcon(meeting.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-white truncate">
                      {meeting.title}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {getStatusText(meeting.status)} • {' '}
                      {new Date(meeting.created_at).toLocaleDateString()}
                      {meeting.duration && ` • ${Math.round(meeting.duration / 60)} min`}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FolderIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                No meetings yet
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Upload your first meeting recording to get started.
              </p>
              <Link
                to="/upload"
                className="btn-primary"
              >
                Upload Meeting
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;