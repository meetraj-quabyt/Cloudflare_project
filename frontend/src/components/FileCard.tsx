import { File as FileIcon } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import type { FileRow } from "../types";

export function FileCard({ file, onClick }: { file: FileRow; onClick: () => void }) {
  return (
    <div onClick={onClick} className="bg-white border rounded-lg p-4 hover:shadow-md cursor-pointer transition">
      <div className="flex items-center gap-3">
        <FileIcon className="w-8 h-8 text-blue-500" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">{file.original_filename}</p>
          <p className="text-xs text-gray-500">{(file.size_bytes / 1024).toFixed(1)} KB · {new Date(file.created_at).toLocaleDateString()}</p>
        </div>
        <StatusBadge status={file.upload_status} />
      </div>
    </div>
  );
}