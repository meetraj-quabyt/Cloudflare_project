import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./pages/Dashboard";
import FileDetails from "./pages/FileDetails";
import PublicShare from "./pages/PublicShare";
import Activity from "./pages/Activity";
import Settings from "./pages/Settings";

const qc = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white border-b px-6 py-3 flex items-center gap-6">
            <Link to="/" className="font-bold text-blue-600 text-lg">CloudShare</Link>
            <Link to="/" className="text-gray-600 hover:text-gray-900 text-sm">Dashboard</Link>
            <Link to="/activity" className="text-gray-600 hover:text-gray-900 text-sm">Activity</Link>
            <Link to="/settings" className="text-gray-600 hover:text-gray-900 text-sm">Settings</Link>
          </nav>
          <main className="max-w-5xl mx-auto px-4 py-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/files/:fileId" element={<FileDetails />} />
              <Route path="/s/:token" element={<PublicShare />} />
              <Route path="/activity" element={<Activity />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}