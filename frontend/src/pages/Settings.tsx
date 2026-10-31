import { useState } from "react";

export default function Settings() {
  const [maxSize, setMaxSize] = useState(100);
  const [expiry, setExpiry] = useState(168);
  const [maxDl, setMaxDl] = useState("");
  return (
    <div className="space-y-6 max-w-md">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      <p className="text-sm text-gray-500">Frontend preferences only. Enforcement happens on the backend.</p>
      <div className="bg-white border rounded-lg p-6 space-y-4">
        <div>
          <label className="text-sm text-gray-700">Default share expiry (hours)</label>
          <input type="number" value={expiry} onChange={(e) => setExpiry(Number(e.target.value))} className="w-full border rounded px-3 py-1.5 mt-1" />
        </div>
        <div>
          <label className="text-sm text-gray-700">Max file size (MB)</label>
          <input type="number" value={maxSize} onChange={(e) => setMaxSize(Number(e.target.value))} className="w-full border rounded px-3 py-1.5 mt-1" />
        </div>
        <div>
          <label className="text-sm text-gray-700">Default download limit (empty = unlimited)</label>
          <input value={maxDl} onChange={(e) => setMaxDl(e.target.value)} className="w-full border rounded px-3 py-1.5 mt-1" />
        </div>
        <p className="text-xs text-gray-400">These are local preferences for the MVP.</p>
      </div>
    </div>
  );
}