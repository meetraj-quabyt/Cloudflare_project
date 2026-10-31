-- CloudShare initial schema (D1 / SQLite compatible)

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    object_key TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    checksum_sha256 TEXT,
    upload_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    uploaded_at TEXT,
    expires_at TEXT,
    deleted_at TEXT,
    owner_token TEXT
);

CREATE TABLE IF NOT EXISTS upload_sessions (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    expected_size_bytes INTEGER NOT NULL,
    actual_size_bytes INTEGER,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    completed_at TEXT,
    failure_reason TEXT
);

CREATE TABLE IF NOT EXISTS share_links (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    max_downloads INTEGER,
    download_count INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS download_sessions (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    share_link_id TEXT NOT NULL REFERENCES share_links(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'initiated',
    created_at TEXT NOT NULL,
    url_issued_at TEXT,
    completed_at TEXT,
    bytes_transferred INTEGER,
    failure_reason TEXT
);

CREATE TABLE IF NOT EXISTS file_events (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    share_link_id TEXT REFERENCES share_links(id) ON DELETE SET NULL,
    upload_session_id TEXT REFERENCES upload_sessions(id) ON DELETE SET NULL,
    download_session_id TEXT REFERENCES download_sessions(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    status TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    bytes_transferred INTEGER,
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at);
CREATE INDEX IF NOT EXISTS idx_files_owner ON files(owner_token);
CREATE INDEX IF NOT EXISTS idx_share_links_file ON share_links(file_id);
CREATE INDEX IF NOT EXISTS idx_share_links_active ON share_links(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_file ON upload_sessions(file_id);
CREATE INDEX IF NOT EXISTS idx_download_sessions_file ON download_sessions(file_id);
CREATE INDEX IF NOT EXISTS idx_download_sessions_share ON download_sessions(share_link_id);
CREATE INDEX IF NOT EXISTS idx_file_events_file ON file_events(file_id);
CREATE INDEX IF NOT EXISTS idx_file_events_occurred ON file_events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_file_events_type ON file_events(event_type);