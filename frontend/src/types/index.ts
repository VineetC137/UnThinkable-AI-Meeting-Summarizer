// API Response Types
export interface APIResponse<T> {
  data?: T;
  error?: {
    code: number;
    message: string;
    type: string;
  };
}

// User Types
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface UserCreate {
  email: string;
  username: string;
  full_name?: string;
  password: string;
  role?: 'admin' | 'user' | 'viewer';
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Meeting Types
export type ProcessingStatus = 'pending' | 'transcribing' | 'summarizing' | 'completed' | 'failed';
export type ASRProvider = 'whisper_cpp' | 'openai_whisper' | 'faster_whisper';
export type LLMProvider = 'ollama' | 'openai' | 'gemini' | 'claude';

export interface Meeting {
  id: number;
  title: string;
  description?: string;
  context?: string;
  tags?: string[];
  original_filename: string;
  file_path: string;
  file_size: number;
  duration?: number;
  
  // Processing configuration
  asr_provider: ASRProvider;
  asr_model: string;
  llm_provider: LLMProvider;
  llm_model: string;
  
  // Processing status
  status: ProcessingStatus;
  processing_started_at?: string;
  processing_completed_at?: string;
  error_message?: string;
  
  // Results
  transcript?: string;
  confidence_score?: number;
  language_detected?: string;
  speaker_segments?: SpeakerSegment[];
  num_speakers?: number;
  summaries?: MeetingSummaries;
  key_decisions?: KeyDecision[];
  action_items?: ActionItem[];
  risks?: Risk[];
  open_questions?: OpenQuestion[];
  keywords?: string[];
  
  // Metadata
  owner_id: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface MeetingCreate {
  title: string;
  description?: string;
  context?: string;
  tags?: string[];
  asr_provider?: ASRProvider;
  asr_model?: string;
  llm_provider?: LLMProvider;
  llm_model?: string;
}

export interface MeetingUpdate {
  title?: string;
  description?: string;
  context?: string;
  tags?: string[];
}

export interface MeetingList {
  meetings: Meeting[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface SpeakerSegment {
  start_time: number;
  end_time: number;
  duration: number;
  text: string;
  primary_speaker: string;
  confidence?: number;
}

export interface ActionItem {
  id: string;
  description: string;
  owner?: string;
  deadline?: string;
  priority?: 'low' | 'medium' | 'high';
  status?: 'open' | 'in_progress' | 'completed';
}

export interface KeyDecision {
  id: string;
  description: string;
  decision_maker?: string;
  rationale?: string;
  timestamp?: string;
}

export interface Risk {
  id: string;
  description: string;
  impact?: 'low' | 'medium' | 'high';
  probability?: 'low' | 'medium' | 'high';
  mitigation?: string;
  category?: string;
}

export interface OpenQuestion {
  id: string;
  question: string;
  context?: string;
  assigned_to?: string;
  urgency?: 'low' | 'medium' | 'high';
}

export interface MeetingSummaries {
  executive_summary?: string;
  detailed_summary?: string;
  key_points?: string[];
}

export interface MeetingAnalytics {
  total_meetings: number;
  total_duration_hours: number;
  avg_processing_time_seconds: number;
  status_breakdown: Record<string, number>;
  provider_usage: Record<string, number>;
  recent_activity: Array<{
    id: number;
    title: string;
    status: ProcessingStatus;
    created_at: string;
    duration?: number;
  }>;
}

// Search and Filter Types
export interface MeetingSearch {
  query?: string;
  tags?: string[];
  status?: ProcessingStatus;
  asr_provider?: ASRProvider;
  llm_provider?: LLMProvider;
  date_from?: string;
  date_to?: string;
  page?: number;
  per_page?: number;
}

// Export Types
export type ExportFormat = 'json' | 'markdown' | 'docx' | 'pdf';

export interface ExportOptions {
  format: ExportFormat;
  include_transcript?: boolean;
  include_summary?: boolean;
  include_action_items?: boolean;
  include_key_decisions?: boolean;
  include_speaker_segments?: boolean;
}

// Processing Status Types
export interface ProcessingStatusInfo {
  meeting_id: number;
  status: ProcessingStatus;
  processing_started_at?: string;
  processing_completed_at?: string;
  processing_time_seconds?: number;
  error_message?: string;
  has_transcript: boolean;
  has_speaker_segments: boolean;
  has_summaries: boolean;
  confidence_score?: number;
  language_detected?: string;
  num_speakers?: number;
}

// Provider Info Types
export interface ProviderInfo {
  available: boolean;
  models: string[];
  description: string;
}

export interface AIProviderStatus {
  transcription_providers: Record<string, ProviderInfo>;
  summarization_providers: Record<string, ProviderInfo>;
  speaker_diarization_available: boolean;
}

// Theme Types
export type Theme = 'light' | 'dark' | 'system';

// UI State Types
export interface UIState {
  theme: Theme;
  sidebarOpen: boolean;
  loading: boolean;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: Date;
}

// Form Types
export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  email: string;
  username: string;
  full_name?: string;
  password: string;
  confirmPassword: string;
}

export interface MeetingUploadForm {
  title: string;
  description?: string;
  context?: string;
  tags: string[];
  asr_provider: ASRProvider;
  asr_model: string;
  llm_provider: LLMProvider;
  llm_model: string;
  audio_file?: File;
}

// Pagination Types
export interface PaginationParams {
  page: number;
  per_page: number;
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// Error Types
export interface APIError {
  code: number;
  message: string;
  type: string;
  details?: Record<string, any>;
}

// Health Check Types
export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  components?: {
    database: string;
    ai_providers: AIProviderStatus;
  };
}

// File Upload Types
export interface FileUploadProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

// Settings Types
export interface UserSettings {
  theme: Theme;
  notifications: {
    email: boolean;
    push: boolean;
    meeting_completed: boolean;
    processing_failed: boolean;
  };
  default_providers: {
    asr_provider: ASRProvider;
    asr_model: string;
    llm_provider: LLMProvider;
    llm_model: string;
  };
  ui: {
    items_per_page: number;
    show_timestamps: boolean;
    auto_refresh: boolean;
  };
}