import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  PlayIcon,
  UserIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { APIClient } from '@/lib/api';
import LoadingSpinner from '@/components/UI/LoadingSpinner';

const MeetingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const meetingId = parseInt(id!);

  const { data: meeting, isLoading } = useQuery(
    ['meeting', meetingId],
    () => APIClient.getMeeting(meetingId),
    { enabled: !!meetingId }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Meeting not found
        </h2>
        <Link to="/meetings" className="btn-primary">
          Back to Meetings
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium';
    
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
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/meetings"
            className="btn-ghost btn-sm"
          >
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            Back to Meetings
          </Link>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn-outline btn-sm">
            <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
            Export
          </button>
          {meeting.status === 'pending' && (
            <button className="btn-primary btn-sm">
              <PlayIcon className="w-4 h-4 mr-2" />
              Start Processing
            </button>
          )}
        </div>
      </div>

      {/* Meeting info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {meeting.title}
            </h1>
            {meeting.description && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {meeting.description}
              </p>
            )}
          </div>
          <span className={getStatusBadge(meeting.status)}>
            {meeting.status.charAt(0).toUpperCase() + meeting.status.slice(1)}
          </span>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="flex items-center space-x-3">
            <ClockIcon className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Duration
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {meeting.duration ? `${Math.round(meeting.duration / 60)} minutes` : 'Unknown'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <UserIcon className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Speakers
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {meeting.num_speakers || 'Unknown'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="w-5 h-5 text-gray-400 flex items-center justify-center">
              <span className="text-xs font-bold">AI</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Processing
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {meeting.asr_provider} + {meeting.llm_provider}
              </p>
            </div>
          </div>
        </div>

        {/* Tags */}
        {meeting.tags && meeting.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {meeting.tags.map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Content tabs */}
      {meeting.status === 'completed' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8 px-6">
              <button className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                Summary
              </button>
              <button className="border-primary-500 text-primary-600 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                Transcript
              </button>
              <button className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                Action Items
              </button>
              <button className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                Key Decisions
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Transcript content */}
            {meeting.transcript ? (
              <div className="prose dark:prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-sm bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                  {meeting.transcript}
                </pre>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">
                  Transcript not available yet.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Processing status */}
      {meeting.status !== 'completed' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Processing Status
          </h2>
          
          {meeting.status === 'failed' ? (
            <div className="text-red-600 dark:text-red-400">
              <p className="font-medium mb-2">Processing Failed</p>
              {meeting.error_message && (
                <p className="text-sm">{meeting.error_message}</p>
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-3">
              <LoadingSpinner size="sm" />
              <span className="text-gray-600 dark:text-gray-400">
                {meeting.status === 'pending' && 'Waiting to start processing...'}
                {meeting.status === 'transcribing' && 'Transcribing audio...'}
                {meeting.status === 'summarizing' && 'Generating summary...'}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MeetingDetailPage;