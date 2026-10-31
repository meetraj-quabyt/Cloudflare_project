import { useState } from "react";
import { Copy, Check } from "lucide-react";

export function ShareLinkDialog({ shareUrl }: { shareUrl: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
      <p className="text-sm font-medium text-blue-900 mb-2">Share link</p>
      <div className="flex gap-2">
        <input readOnly value={shareUrl} className="flex-1 text-sm border rounded px-2 py-1 bg-white" />
        <button onClick={copy} className="px-3 py-1 bg-blue-600 text-white rounded text-sm flex items-center gap-1">
          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />} Copy
        </button>
      </div>
    </div>
  );
}