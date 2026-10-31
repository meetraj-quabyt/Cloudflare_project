import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { ActivityTable } from "../components/ActivityTable";
import { getOwnerToken } from "../utils/owner";

export default function Activity() {
  const owner = getOwnerToken();
  const [fileId, setFileId] = useState("");
  const [eventType, setEventType] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const q = useQuery({
    queryKey: ["activity", owner, fileId, eventType, page],
    queryFn: () => {
      const params = new URLSearchParams({ owner_token: owner, limit: String(limit), offset: String(page * limit) });
      if (fileId) params.set("file_id", fileId);
      if (eventType) params.set("event_type", eventType);
      return api.get(`/api/v1/activity?${params.toString()}`);
    },
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Activity</h1>
      <div className="flex gap-3">
        <input value={fileId} onChange={(e) => setFileId(e.target.value)} placeholder="Filter by file id" className="border rounded px-3 py-1.5 text-sm" />
        <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="border rounded px-3 py-1.5 text-sm">
          <option value="">All events</option>
          <option value="upload_completed">upload_completed</option>
          <option value="download_initiated">download_initiated</option>
          <option value="download_url_issued">download_url_issued</option>
          <option value="download_client_reported_complete">download_client_reported_complete</option>
          <option value="download_failed">download_failed</option>
          <option value="link_created">link_created</option>
          <option value="link_revoked">link_revoked</option>
        </select>
      </div>
      {q.isLoading && <p className="text-gray-500">Loading...</p>}
      {q.isError && <p className="text-red-600">{(q.error as Error).message}</p>}
      {q.data && <ActivityTable events={q.data.items} />}
      {q.data && (
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500">Total: {q.data.total}</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))} className="px-3 py-1 border rounded disabled:opacity-50">Prev</button>
            <button disabled={(page + 1) * limit >= q.data.total} onClick={() => setPage((p) => p + 1)} className="px-3 py-1 border rounded disabled:opacity-50">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}