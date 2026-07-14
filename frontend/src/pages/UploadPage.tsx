import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-hot-toast';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { APIClient } from '@/lib/api';
import { MeetingUploadForm } from '@/types';
import LoadingSpinner from '@/components/UI/LoadingSpinner';

const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<MeetingUploadForm>({
    defaultValues: {
      asr_provider: 'whisper_cpp',
      asr_model: 'small',
      llm_provider: 'ollama',
      llm_model: 'llama2',
      tags: [],
    },
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac'],
    },
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
        // Auto-fill title if empty
        const currentTitle = watch('title');
        if (!currentTitle) {
          const fileName = acceptedFiles[0].name.replace(/\.[^/.]+$/, '');
          setValue('title', fileName);
        }
      }
    },
  });

  const removeFile = () => {
    setSelectedFile(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const onSubmit = async (data: MeetingUploadForm) => {
    if (!selectedFile) {
      toast.error('Please select an audio file');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);

      const meeting = await APIClient.createMeeting(
        {
          title: data.title,
          description: data.description,
          context: data.context,
          tags: data.tags,
          asr_provider: data.asr_provider,
          asr_model: data.asr_model,
          llm_provider: data.llm_provider,
          llm_model: data.llm_model,
        },
        selectedFile,
        (progress) => setUploadProgress(progress)
      );

      toast.success('Meeting uploaded successfully!');
      navigate(`/meetings/${meeting.id}`);
    } catch (error) {
      toast.error('Failed to upload meeting');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Upload Meeting
        </h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Upload an audio recording to generate AI-powered transcripts and summaries.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* File upload */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Audio File
          </h2>
          
          {!selectedFile ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500'
              }`}
            >
              <input {...getInputProps()} />
              <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {isDragActive ? 'Drop your file here' : 'Upload audio file'}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Drag and drop your audio file here, or click to browse
              </p>
              <p className="text-sm text-gray-400">
                Supports MP3, WAV, M4A, OGG, FLAC, AAC (max 100MB)
              </p>
            </div>
          ) : (
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <DocumentIcon className="w-8 h-8 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              
              {uploading && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Meeting details */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Meeting Details
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="label">
                Title *
              </label>
              <input
                {...register('title', { required: 'Title is required' })}
                type="text"
                className="input mt-1"
                placeholder="Enter meeting title"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.title.message}
                </p>
              )}
            </div>

            <div className="md:col-span-2">
              <label className="label">
                Description
              </label>
              <textarea
                {...register('description')}
                className="textarea mt-1"
                rows={3}
                placeholder="Optional description"
              />
            </div>

            <div className="md:col-span-2">
              <label className="label">
                Context
              </label>
              <textarea
                {...register('context')}
                className="textarea mt-1"
                rows={3}
                placeholder="Provide context to improve summary quality (e.g., meeting type, participants, agenda)"
              />
            </div>
          </div>
        </div>

        {/* AI Configuration */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            AI Processing Settings
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="label">
                Speech-to-Text Provider
              </label>
              <select
                {...register('asr_provider')}
                className="input mt-1"
              >
                <option value="whisper_cpp">Whisper.cpp (Local)</option>
                <option value="openai_whisper">OpenAI Whisper</option>
                <option value="faster_whisper">Faster Whisper</option>
              </select>
            </div>

            <div>
              <label className="label">
                ASR Model
              </label>
              <select
                {...register('asr_model')}
                className="input mt-1"
              >
                <option value="small">Small (Fast)</option>
                <option value="base">Base (Balanced)</option>
                <option value="medium">Medium (Better)</option>
                <option value="large">Large (Best)</option>
              </select>
            </div>

            <div>
              <label className="label">
                Summarization Provider
              </label>
              <select
                {...register('llm_provider')}
                className="input mt-1"
              >
                <option value="ollama">Ollama (Local)</option>
                <option value="openai">OpenAI GPT</option>
                <option value="gemini">Google Gemini</option>
                <option value="claude">Anthropic Claude</option>
              </select>
            </div>

            <div>
              <label className="label">
                LLM Model
              </label>
              <select
                {...register('llm_model')}
                className="input mt-1"
              >
                <option value="llama2">Llama 2</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="gpt-4">GPT-4</option>
              </select>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/meetings')}
            className="btn-outline"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={uploading || !selectedFile}
            className="btn-primary"
          >
            {uploading ? (
              <div className="flex items-center">
                <LoadingSpinner size="sm" className="mr-2" />
                Uploading...
              </div>
            ) : (
              'Upload & Process'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default UploadPage;