import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import {
  LayoutDashboard,
  Users,
  FileText,
  Settings,
  LogOut,
  Menu,
  Shield,
  Building2,
  BarChart3
} from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Clients', path: '/clients', icon: Users },
    { label: 'Visa Applications', path: '/submissions', icon: FileText },
    { label: 'Reports', path: '/reports', icon: BarChart3 },
  ];

  // Show Admin link only for admins
  if (user && (user.role === 'SUPER_ADMIN' || user.role === 'AGENCY_ADMIN')) {
    navItems.push({ label: 'Admin Rules', path: '/admin', icon: Settings });
  }

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex h-screen bg-[#070b13] overflow-hidden text-slate-100 font-sans">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex md:flex-col md:w-64 bg-[#0a0e1a] border-r border-slate-800/60 p-4 shrink-0 justify-between">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-2 px-2 py-4 mb-6">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
              V
            </div>
            <div>
              <span className="font-extrabold text-lg bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">VisaFlow</span>
              <span className="text-xs font-bold text-indigo-400 ml-1">AI</span>
            </div>
          </div>

          {/* Org Info */}
          {user?.organization_name && (
            <div className="flex items-center gap-2 px-3 py-2.5 mb-6 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <div className="truncate text-xs font-semibold text-slate-300">
                {user.organization_name}
              </div>
            </div>
          )}

          {/* Nav Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    active 
                      ? 'bg-gradient-to-r from-indigo-600/30 to-violet-600/20 text-indigo-400 border border-indigo-500/20' 
                      : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-indigo-400' : 'text-slate-400'}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer profile info & Logout */}
        <div className="pt-4 border-t border-slate-800/60">
          <div className="flex items-center gap-3 px-2 mb-4">
            <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-semibold text-indigo-400">
              {user?.first_name ? user.first_name[0].toUpperCase() : user?.email[0].toUpperCase()}
            </div>
            <div className="truncate flex-1">
              <div className="text-xs font-semibold text-slate-200">
                {user?.first_name ? `${user.first_name} ${user.last_name}` : 'Consultant'}
              </div>
              <div className="text-[10px] text-slate-400 truncate">{user?.email}</div>
            </div>
            <div className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-0.5 shrink-0">
              <Shield className="w-2.5 h-2.5 text-indigo-400" />
              {user?.role === 'SUPER_ADMIN' ? 'Admin' : user?.role === 'AGENCY_ADMIN' ? 'Owner' : 'Staff'}
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/5 transition-all duration-150"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile Nav Top Bar */}
      <div className="md:hidden flex flex-col w-full h-full">
        <header className="flex items-center justify-between p-4 bg-[#0a0e1a] border-b border-slate-800/60 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white">
              V
            </div>
            <span className="font-extrabold text-md text-slate-100">VisaFlow</span>
          </div>
          <button 
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-1 rounded bg-slate-800 border border-slate-700 text-slate-200"
          >
            <Menu className="w-5 h-5" />
          </button>
        </header>

        {/* Mobile menu dropdown */}
        {mobileOpen && (
          <div className="bg-[#0a0e1a] border-b border-slate-800/80 p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                    isActive(item.path) ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-rose-400"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        )}

        {/* Mobile Workspace Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>

      {/* Desktop Workspace Content */}
      <main className="hidden md:block flex-1 overflow-y-auto p-8 bg-[#070b13]">
        {children}
      </main>
    </div>
  );
}
