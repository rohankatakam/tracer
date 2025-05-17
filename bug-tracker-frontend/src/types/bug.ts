export enum SeverityLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface Bug {
  bug_id: string;
  title: string;
  description: string;
  reporter: string;
  severity: SeverityLevel;
  created_at: string;
  updated_at: string;
  attachment_count?: number;
  attachments?: Attachment[];
}

export interface CreateBugRequest {
  title: string;
  description: string;
  reporter: string;
  severity: SeverityLevel;
}

export interface UpdateBugRequest {
  title?: string;
  description?: string;
  reporter?: string;
  severity?: SeverityLevel;
}

export interface Attachment {
  attachment_id: string;
  bug_id: string;
  filename: string;
  file_type?: string;
  file_extension?: string;
  file_size: number;
  content_type?: string;
  upload_timestamp: string;
  processing_status: string;
  processing_error?: string | null;
  description?: string | null;
  uploader?: string | null;
  content?: {
    text_content_ids: string[];
    image_content_ids: string[];
    pdf_content_id: string | null;
    video_content_id: string | null;
  };
  metadata?: Record<string, any>;
}
