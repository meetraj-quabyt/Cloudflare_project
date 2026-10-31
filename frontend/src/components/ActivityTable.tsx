import type { ActivityEvent } from "../types";

export function ActivityTable({ events }: { events: ActivityEvent[] }) {
  if (!events.length) return <p className="text-sm text-gray-500">No events.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-gray-500 border-b">
          <tr><th className="py-2">Time</th><th>File</th><th>Event</th><th>Status</th><th>Bytes</th></tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id} className="border-b last:border-0">
              <td className="py-2 text-gray-600">{new Date(e.occurred_at).toLocaleString()}</td>
              <td className="py-2 font-mono text-xs">{e.file_id.slice(0, 8)}</td>
              <td className="py-2">{e.event_type}</td>
              <td className="py-2">{e.status}</td>
              <td className="py-2">{e.bytes_transferred ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}