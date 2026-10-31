export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="text-center py-8">
      <p className="text-red-600 text-sm">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 px-3 py-1.5 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100">
          Retry
        </button>
      )}
    </div>
  );
}