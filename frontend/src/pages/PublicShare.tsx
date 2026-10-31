import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import { DownloadButton } from "../components/DownloadButton";
import { ErrorState } from "../components/ErrorState";
import { formatBytes } from "../utils/format";

export default function PublicShare() {
  const { token } = useParams();
  const infoQ = useQuery({
    queryKey: ["share", token],
    queryFn: () => api.get(`/api/v1/shares/${token}`),
    enabled: !!token,
    retry: false,
  });

  const dlMut = useMutation({
    mutationFn: async () => {
      const data: any = await api.post(`/api/v1/shares/${token}/downloads`);
      // trigger download
      const a = document.createElement("a");
      a.href = data.download_url;
      a.download = data.file_name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      // report completion after a delay
      setTimeout(() => {
        api.post(`/api/v1/downloads/${data.download_session_id}/complete`, { bytes_transferred: data.size_bytes }).catch(() => {});
      }, 1000);
      return data;
    },
  });

  if (infoQ.isLoading) return <p className="text-gray-500">Loading...</p>;
  if (infoQ.isError) {
    const msg = (infoQ.error as Error).message;
    if (msg.includes("expired")) return <div className="text-center py-12"><h2 className="text-xl font-bold">Link expired</h2><p className="text-gray-500 mt-2">This share link has expired.</p></div>;
    if (msg.includes("revoked")) return <div className="text-center py-12"><h2 className="text-xl font-bold">Link revoked</h2><p className="text-gray-500 mt-2">This share link is no longer active.</p></div>;
    return <ErrorState message={msg} onRetry={() => infoQ.refetch()} />;
  }
  const info = infoQ.data as any;

  return (
    <div className="max-w-md mx-auto bg-white border rounded-lg p-6 space-y-4">
      <h1 className="text-xl font-bold text-gray-900">{info.file_name}</h1>
      <p className="text-sm text-gray-600">Size: {formatBytes(info.size_bytes)}</p>
      <p className="text-sm text-gray-600">Type: {info.content_type}</p>
      {info.upload_date && <p className="text-sm text-gray-600">Uploaded: {new Date(info.upload_date).toLocaleDateString()}</p>}
      {info.expires_at && <p className="text-sm text-gray-600">Expires: {new Date(info.expires_at).toLocaleString()}</p>}
      {info.remaining_downloads != null && <p className="text-sm text-gray-600">Remaining downloads: {info.remaining_downloads}</p>}
      <DownloadButton onClick={() => dlMut.mutate()} disabled={dlMut.isPending} />
      {dlMut.isError && <p className="text-sm text-red-600">{(dlMut.error as Error).message}</p>}
      {dlMut.isSuccess && <p className="text-sm text-green-600">Download started.</p>}
    </div>
  );
}