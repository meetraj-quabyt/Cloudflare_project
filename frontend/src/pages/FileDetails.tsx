import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { ShareLinkDialog } from "../components/ShareLinkDialog";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EmptyState } from "../components/EmptyState";
import { getOwnerToken } from "../utils/owner";
import { formatBytes, relTime } from "../utils/format";

export default function FileDetails() {
  const { fileId } = useParams();
  const owner = getOwnerToken();
  const qc = useQueryClient();
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [confirm, setConfirm] = useState(false);

  const q = useQuery({
    queryKey: ["file", fileId, owner],
    queryFn: () => api.get(`/api/v1/files/${fileId}?owner_token=${owner}`),
    enabled: !!fileId,
  });

  const revokeMut = useMutation({
    mutationFn: (shareId: string) => api.post(`/api/v1/shares/${shareId}/revoke`, { owner_token: owner }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["file", fileId, owner] }),
  });

  const createShareMut = useMutation({
    mutationFn: () => api.post(`/api/v1/files/${fileId}/share`, { owner_token: owner }),
    onSuccess: (data: any) => {
      setShareUrl(data.share_url);
      qc.invalidateQueries({ queryKey: ["file", fileId, owner] });
    },
  });

  const deleteMut = useMutation({
    mutationFn: () => api.del(`/api/v1/files/${fileId}?owner_token=${owner}`),
    onSuccess: () => { window.location.href = "/"; },
  });

  if (q.isLoading) return <p className="text-gray-500">Loading...</p>;
  if (q.isError) return <p className="text-red-600">{(q.error as Error).message}</p>;
  const data = q.data;
  const file = data.file;
  const links = data.share_links || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{file.original_filename}</h1>
      <div className="bg-white border rounded-lg p-6 space-y-2">
        <p><span className="text-gray-500">Size:</span> {formatBytes(file.size_bytes)}</p>
        <p><span className="text-gray-500">Type:</span> {file.content_type}</p>
        <p><span className="text-gray-500">Uploaded:</span> {file.uploaded_at ? relTime(file.uploaded_at) : "-"}</p>
        <p><span className="text-gray-500">Status:</span> <StatusBadge status={file.upload_status} /></p>
      </div>

      <div className="bg-white border rounded-lg p-6 space-y-3">
        <h2 className="font-semibold">Share links</h2>
        <button onClick={() => createShareMut.mutate()} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm">
          Create / Rotate link
        </button>
        {shareUrl && <ShareLinkDialog shareUrl={shareUrl} />}
        {links.length === 0 && <EmptyState title="No share links" />}
        {links.map((l: any) => (
          <div key={l.id} className="flex items-center justify-between border rounded p-3 text-sm">
            <div>
              <p>Downloads: {l.download_count}{l.max_downloads ? ` / ${l.max_downloads}` : ""}</p>
              <p className="text-gray-500">Expires: {l.expires_at ? new Date(l.expires_at).toLocaleString() : "never"}</p>
              <p>Active: {l.is_active ? "yes" : "no"}</p>
            </div>
            {l.is_active && (
              <button onClick={() => revokeMut.mutate(l.id)} className="px-3 py-1 text-red-600 border border-red-200 rounded text-xs">
                Revoke
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="bg-white border rounded-lg p-6">
        <h2 className="font-semibold mb-2">Recent events</h2>
        <ul className="text-sm space-y-1">
          {(data.recent_events || []).map((e: any) => (
            <li key={e.id} className="text-gray-600">{e.event_type} · {e.status} · {new Date(e.occurred_at).toLocaleString()}</li>
          ))}
        </ul>
      </div>

      <button onClick={() => setConfirm(true)} className="px-4 py-2 bg-red-600 text-white rounded-md text-sm">Delete file</button>
      <ConfirmDialog open={confirm} title="Delete file" message="This will revoke links and remove the file." onConfirm={() => deleteMut.mutate()} onCancel={() => setConfirm(false)} />
    </div>
  );
}