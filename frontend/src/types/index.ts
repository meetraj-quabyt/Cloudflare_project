export interface FileRow {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  upload_status: string;
  created_at: string;
  uploaded_at?: string | null;
  expires_at?: string | null;
  owner_token?: string | null;
}

export interface ShareLink {
  id: string;
  file_id: string;
  created_at: string;
  expires_at?: string | null;
  max_downloads?: number | null;
  download_count: number;
  is_active: number | boolean;
  revoked_at?: string | null;
}

export interface UploadInitResponse {
  session_id: string;
  file_id: string;
  upload_url: string;
  upload_method: string;
  required_headers: Record<string, string>;
  expires_at: string;
}

export interface PublicShareInfo {
  file_name: string;
  size_bytes: number;
  content_type: string;
  upload_date?: string | null;
  expires_at?: string | null;
  remaining_downloads?: number | null;
  is_active: boolean;
}

export interface DownloadInitResponse {
  download_session_id: string;
  download_url: string;
  expires_at: string;
  file_name: string;
  size_bytes: number;
}

export interface ActivityEvent {
  id: string;
  file_id: string;
  event_type: string;
  status: string;
  occurred_at: string;
  bytes_transferred?: number | null;
  metadata_json?: string | null;
}

export interface ActivityResponse {
  items: ActivityEvent[];
  total: number;
  limit: number;
  offset: number;
}