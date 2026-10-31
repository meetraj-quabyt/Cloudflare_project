import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { FileDropzone } from "../components/FileDropzone";
import { UploadProgress } from "../components/UploadProgress";
import { FileCard } from "../components/FileCard";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { ShareLinkDialog } from "../components/ShareLinkDialog";
import { getOwnerToken } from "../utils/owner";
import { formatBytes } from "../utils/format";
import type { FileRow, UploadInitResponse } from "../types";
import { useNavigate } from "react-router-dom";

const MAX = 100 * 1024 * 1024;

export default function Dashboard() {
  const owner = getOwnerToken();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filesQ = useQuery({
    queryKey: ["files", owner],
    queryFn: () => api.get(`/api/v1/files?owner_token=${owner}`),
  });

  const totalsQ = useQuery({
    queryKey: ["totals", owner],
    queryFn: async () => {
      const data: any = await api.get(`/api/v1/files?owner_token=${owner}&limit=1`);
      const acts: any = await api.get(`/api/v1/activity?owner_token=${owner}&limit=1`);
      return { files: data.total, activity: acts.total };
    },
  });

  const handleFile = (f: File) => {
    setError(null);
    setShareUrl(null);
    if (f.size > MAX) { setError("File too large (max 100MB)"); return; }
    setFile(f);
  };

  const upload = async () => {
    if (!file) return;
    setError(null);
    setStatus("Initiating...");
    try {
      const init: UploadInitResponse = await api.post("/api/v1/uploads/initiate", {
        filename: file.name,
        content_type: file.type || "application/octet-stream",
        size_bytes: file.size,
        owner_token: owner,
      });
      setStatus("Uploading...");
      // upload via XHR for progress
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const method = (init.upload_method || "PUT").toUpperCase();
        xhr.open(method, init.upload_url);
        if (method === "PUT") {
          xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");
          for (const [k, v] of Object.entries(init.required_headers || {})) xhr.setRequestHeader(k, v as string);
        }
        xhr.upload.onprogress = (e) => { if (e.lengthComputable) setProgress((e.loaded / e.total) * 100); };
        xhr.onload = () => { if (xhr.status >= 200 && xhr.status < 300) resolve(); else reject(new Error("Upload failed")); };
        xhr.onerror = () => reject(new Error("Network error"));
        xhr.send(file);
      });
      setStatus("Verifying...");
      const res: any = await api.post(`/api/v1/uploads/${init.session_id}/complete`, {});
      setStatus("Done");
      setShareUrl(res.share_url);
      qc.invalidateQueries({ queryKey: ["files", owner] });
      setFile(null);
      setProgress(0);
    } catch (e: any) {
      setError(e.message || "Upload failed");
      setStatus("");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <p className="text-sm text-gray-500">Total files</p>
          <p className="text-2xl font-bold">{totalsQ.data?.files ?? "-"}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <p className="text-sm text-gray-500">Storage used</p>
          <p className="text-2xl font-bold">{formatBytes((filesQ.data?.items || []).reduce((a: number, f: FileRow) => a + f.size_bytes, 0))}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <p className="text-sm text-gray-500">Activity events</p>
          <p className="text-2xl font-bold">{totalsQ.data?.activity ?? "-"}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg border space-y-4">
        <h2 className="font-semibold text-gray-900">Upload a file</h2>
        <FileDropzone onFile={handleFile} />
        {file && (
          <div className="space-y-2">
            <p className="text-sm text-gray-700">{file.name} ({formatBytes(file.size)})</p>
            <UploadProgress progress={progress} />
            <button onClick={upload} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              Upload
            </button>
          </div>
        )}
        {status && <p className="text-sm text-gray-500">{status}</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
        {shareUrl && <ShareLinkDialog shareUrl={shareUrl} />}
      </div>

      <div className="space-y-3">
        <h2 className="font-semibold text-gray-900">Recent uploads</h2>
        {filesQ.isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {filesQ.isError && <ErrorState message={(filesQ.error as Error).message} onRetry={() => filesQ.refetch()} />}
        {filesQ.data?.items?.length === 0 && <EmptyState title="No files yet" description="Upload your first file to get started." />}
        <div className="grid gap-3">
          {(filesQ.data?.items || []).map((f: FileRow) => (
            <FileCard key={f.id} file={f} onClick={() => navigate(`/files/${f.id}`)} />
          ))}
        </div>
      </div>
    </div>
  );
}