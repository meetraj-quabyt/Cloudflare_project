import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sparkles, FolderUp, Activity as ActivityIcon, Settings as SettingsIcon } from "lucide-react";
import AiChat from "./pages/AiChat";
import Dashboard from "./pages/Dashboard";
import FileDetails from "./pages/FileDetails";
import PublicShare from "./pages/PublicShare";
import Activity from "./pages/Activity";
import Settings from "./pages/Settings";

const qc = new QueryClient();

function Navigation() {
  const location = useLocation();

  const links = [
    { to: "/", label: "AI Agent Workspace", icon: Sparkles, highlight: true },
    { to: "/files", label: "File Share", icon: FolderUp },
    { to: "/activity", label: "D1 Activity", icon: ActivityIcon },
    { to: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-2.5 flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-6">
        <Link to="/" className="flex items-center gap-2 font-bold text-gray-900 text-lg">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
            <Sparkles className="w-4 h-4" />
          </div>
          <span>Cloudflare<span className="text-blue-600">AI</span></span>
        </Link>

        <div className="flex items-center gap-1">
          {links.map((link) => {
            const isActive = location.pathname === link.to;
            const Icon = link.icon;
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? link.highlight
                      ? "bg-blue-50 text-blue-700"
                      : "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
                {link.highlight && (
                  <span className="bg-blue-100 text-blue-700 text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase">
                    New
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span>Cloudflare Edge • D1 SQL</span>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Navigation />
          <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6">
            <Routes>
              <Route path="/" element={<AiChat />} />
              <Route path="/ai" element={<AiChat />} />
              <Route path="/files" element={<Dashboard />} />
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
