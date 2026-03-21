import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, useAuth, API } from "@/App";
import { toast } from "sonner";

// Components
import StatsCards from "@/components/dashboard/StatsCards";
import PnLChart from "@/components/dashboard/PnLChart";
import PositionsTable from "@/components/dashboard/PositionsTable";
import TradeHistory from "@/components/dashboard/TradeHistory";
import ActivityFeed from "@/components/dashboard/ActivityFeed";
import Watchlist from "@/components/dashboard/Watchlist";
import Header from "@/components/dashboard/Header";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { logout, username, token } = useAuth();
  
  const [dashboardData, setDashboardData] = useState(null);
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [activity, setActivity] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [treasuryHistory, setTreasuryHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [wsConnected, setWsConnected] = useState(false);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!token) return;

    const connectWebSocket = () => {
      // Convert HTTP URL to WebSocket URL
      // API is like https://domain.com/api, we need wss://domain.com/ws/token
      const baseUrl = API.replace('/api', '');
      const wsUrl = baseUrl.replace('https://', 'wss://').replace('http://', 'ws://') + `/ws/${token}`;
      
      console.log('Attempting WebSocket connection to:', wsUrl);
      
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('WebSocket connected successfully');
          setWsConnected(true);
          toast.success('Real-time connection established');
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'init' || message.type === 'update' || message.type === 'sync_update') {
              const data = message.data;
              if (data.positions) setPositions(data.positions);
              if (data.trades) setTrades(data.trades);
              if (data.watchlist) setWatchlist(data.watchlist);
              if (data.stats) {
                setDashboardData(prev => ({ ...prev, ...data.stats }));
              }
              setLastRefresh(new Date());
            } else if (message.type === 'heartbeat') {
              // Respond to heartbeat
              ws.send(JSON.stringify({ type: 'pong' }));
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          // Reconnect after 5 seconds
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          ws.close();
        };
      } catch (e) {
        console.error('Failed to create WebSocket:', e);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [token]);

  const fetchData = useCallback(async () => {
    try {
      const [
        dashRes,
        posRes,
        tradesRes,
        activityRes,
        watchRes,
        treasuryRes
      ] = await Promise.all([
        apiClient.get("/dashboard"),
        apiClient.get("/positions"),
        apiClient.get("/trades?limit=50"),
        apiClient.get("/activity?limit=30"),
        apiClient.get("/watchlist"),
        apiClient.get("/treasury/history?days=30")
      ]);

      setDashboardData(dashRes.data);
      setPositions(posRes.data);
      setTrades(tradesRes.data);
      setActivity(activityRes.data);
      setWatchlist(watchRes.data);
      setTreasuryHistory(treasuryRes.data);
      setLastRefresh(new Date());
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      if (error.response?.status !== 401) {
        toast.error("Failed to load dashboard data");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleRefresh = () => {
    setIsLoading(true);
    fetchData();
  };

  if (isLoading && !dashboardData) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-zinc-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950" data-testid="dashboard-page">
      <Header 
        username={username}
        onLogout={handleLogout}
        onRefresh={handleRefresh}
        lastRefresh={lastRefresh}
        isLoading={isLoading}
        botStatus={dashboardData}
        wsConnected={wsConnected}
      />

      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Stats Cards */}
        <StatsCards data={dashboardData} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <PnLChart data={treasuryHistory} />
          </div>
          <div>
            <ActivityFeed activities={activity} />
          </div>
        </div>

        {/* Positions & Watchlist Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PositionsTable positions={positions} />
          <Watchlist tokens={watchlist} />
        </div>

        {/* Trade History */}
        <TradeHistory trades={trades} />
      </main>
    </div>
  );
}
