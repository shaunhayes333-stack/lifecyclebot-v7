import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, useAuth } from "@/App";
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
  const { logout, username } = useAuth();
  
  const [dashboardData, setDashboardData] = useState(null);
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [activity, setActivity] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [treasuryHistory, setTreasuryHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

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
