import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function Header({ username, onLogout, onRefresh, lastRefresh, isLoading, botStatus }) {
  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <header className="bg-zinc-900/50 border-b border-zinc-800 sticky top-0 z-50 backdrop-blur-xl">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Lifecycle Bot</h1>
              <p className="text-xs text-zinc-500">Trading Dashboard</p>
            </div>
          </div>

          {/* Center - Bot Status */}
          <div className="hidden md:flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${botStatus?.bot_running ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-600'}`} />
              <span className="text-sm text-zinc-400">
                {botStatus?.bot_running ? 'Bot Running' : 'Bot Stopped'}
              </span>
            </div>
            {botStatus?.bot_mode && (
              <Badge 
                variant="outline" 
                className={`${
                  botStatus.bot_mode === 'AUTO' ? 'border-emerald-500 text-emerald-400' :
                  botStatus.bot_mode === 'LAUNCH_SNIPE' ? 'border-orange-500 text-orange-400' :
                  botStatus.bot_mode === 'RANGE_TRADE' ? 'border-blue-500 text-blue-400' :
                  'border-zinc-600 text-zinc-400'
                }`}
              >
                {botStatus.bot_mode}
              </Badge>
            )}
          </div>

          {/* Right - User & Actions */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm text-zinc-300">{username}</span>
              <span className="text-xs text-zinc-500">
                Updated: {formatTime(lastRefresh)}
              </span>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
              className="text-zinc-400 hover:text-white hover:bg-zinc-800"
              data-testid="refresh-btn"
            >
              <svg 
                className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={onLogout}
              className="text-zinc-400 hover:text-red-400 hover:bg-zinc-800"
              data-testid="logout-btn"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
