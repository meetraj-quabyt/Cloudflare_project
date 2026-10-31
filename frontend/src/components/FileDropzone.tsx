import { useState, useRef } from "react";
import { UploadCloud } from "lucide-react";

export function FileDropzone({ onFile }: { onFile: (f: File) => void }) {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files?.[0]; if (f) onFile(f); }}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${drag ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}`}
    >
      <UploadCloud className="w-10 h-10 mx-auto text-gray-400" />
      <p className="mt-2 text-sm text-gray-600">Drag & drop a file or click to browse</p>
      <input ref={inputRef} type="file" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }} />
    </div>
  );
}