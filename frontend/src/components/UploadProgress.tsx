export function UploadProgress({ progress }: { progress: number }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
      <div className="bg-blue-600 h-2 transition-all" style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} />
    </div>
  );
}