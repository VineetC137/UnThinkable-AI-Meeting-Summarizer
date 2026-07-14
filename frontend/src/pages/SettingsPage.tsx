import React from 'react';
import { useUIStore, useTheme } from '@/stores/ui';

const SettingsPage: React.FC = () => {
  const theme = useTheme();
  const { setTheme } = useUIStore();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Customize your experience and preferences.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Appearance
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="label">Theme</label>
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as any)}
              className="input mt-1 w-48"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="system">System</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AI Preferences
        </h2>
        
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            Configure your default AI processing settings for new meetings.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Default ASR Provider</label>
              <select className="input mt-1">
                <option value="whisper_cpp">Whisper.cpp (Local)</option>
                <option value="openai_whisper">OpenAI Whisper</option>
                <option value="faster_whisper">Faster Whisper</option>
              </select>
            </div>
            
            <div>
              <label className="label">Default LLM Provider</label>
              <select className="input mt-1">
                <option value="ollama">Ollama (Local)</option>
                <option value="openai">OpenAI GPT</option>
                <option value="gemini">Google Gemini</option>
                <option value="claude">Anthropic Claude</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;