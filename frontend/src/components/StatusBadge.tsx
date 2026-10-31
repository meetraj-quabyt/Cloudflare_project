import { CheckCircle2, Clock, XCircle, AlertTriangle } from "lucide-react";

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; icon: any }> = {
    completed: { color: "bg-green-100 text-green-700", icon: CheckCircle2 },
    pending: { color: "bg-yellow-100 text-yellow-700", icon: Clock },
    failed: { color: "bg-red-100 text-red-700", icon: XCircle },
    expired: { color: "bg-gray-100 text-gray-700", icon: AlertTriangle },
    initiated: { color: "bg-blue-100 text-blue-700", icon: Clock },
    URL_issued: { color: "bg-blue-100 text-blue-700", icon: Clock },
    client_reported_complete: { color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  };
  const { color, icon: Icon } = map[status] || { color: "bg-gray-100 text-gray-600", icon: Clock };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      <Icon className="w-3 h-3" /> {status}
    </span>
  );
}