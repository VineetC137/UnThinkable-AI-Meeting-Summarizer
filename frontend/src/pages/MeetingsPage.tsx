import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { APIClient } from '@/lib/api';
import { MeetingSearch } from '@/types';
import LoadingSpinner from '@/components/UI/LoadingSpinner';

const MeetingsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useState<MeetingSearch>({
    page: 1,
    per_page: 20,
  });

  const { data: meetingsData, isLoading } = useQuery(
    ['meetings', searchParams],
    () => APIClient.getMeetings(searchParams),
    { keepPreviousData: true }
  );

  const getStatusBadge = (status: string) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    switch (status) {
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300`;
      case 'pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300`;
      case 'transcribing':
      case 'summarizing':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Meetings
          </h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Manage your meeting recordings and summaries
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            to="/upload"
            className="btn-primary inline-flex items-center"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Upload Meeting
          </Link>
        </div>
      </div>

      {/* Search and filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
          {/* Search bar */}
          <div className="relative flex-1 max-w-lg">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search meetings..."
              className="input pl-10"
              value={searchParams.query || ''}
              onChange={(e) =>
                setSearchParams({ ...searchParams, query: e.target.value, page: 1 })
              }
            />
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4">
            <button className="btn-outline inline-flex items-center">
              <FunnelIcon className="w-4 h-4 mr-2" />
              Filters
            </button>
          </div>
        </div>
      </div>

      {/* Meetings list */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        {isLoading ? (
          <div className="p-6">
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                    <div className="w-20 h-6 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : meetingsData?.meetings?.length ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {meetingsData.meetings.map((meeting) => (
              <Link
                key={meeting.id}
                to={`/meetings/${meeting.id}`}
                className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
                      <span className="text-primary-600 dark:text-primary-400 font-semibold text-sm">
                        {meeting.title.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {meeting.title}
                      </h3>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                        <span>
                          {new Date(meeting.created_at).toLocaleDateString()}
                        </span>
                        {meeting.duration && (
                          <span>{Math.round(meeting.duration / 60)} min</span>
                        )}
                        {meeting.num_speakers && (
                          <span>{meeting.num_speakers} speakers</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={getStatusBadge(meeting.status)}>
                      {meeting.status.charAt(0).toUpperCase() + meeting.status.slice(1)}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="w-24 h-24 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <MagnifyingGlassIcon className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              No meetings found
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {searchParams.query
                ? 'Try adjusting your search terms or filters.'
                : 'Upload your first meeting to get started.'}
            </p>
            <Link
              to="/upload"
              className="btn-primary"
            >
              Upload Meeting
            </Link>
          </div>
        )}

        {/* Pagination */}
        {meetingsData && meetingsData.pages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Showing {((meetingsData.page - 1) * meetingsData.per_page) + 1} to{' '}
                {Math.min(meetingsData.page * meetingsData.per_page, meetingsData.total)} of{' '}
                {meetingsData.total} results
              </p>
              <div className="flex items-center space-x-2">
                <button
                  disabled={meetingsData.page <= 1}
                  onClick={() =>
                    setSearchParams({ ...searchParams, page: meetingsData.page - 1 })
                  }
                  className="btn-outline btn-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  disabled={meetingsData.page >= meetingsData.pages}
                  onClick={() =>
                    setSearchParams({ ...searchParams, page: meetingsData.page + 1 })
                  }
                  className="btn-outline btn-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MeetingsPage;