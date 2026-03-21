import { Card, CardContent } from "@/components/ui/card";

export default function StatsCards({ data }) {
  if (!data) return null;

  const stats = [
    {
      label: "Treasury",
      value: `${data.treasury_sol?.toFixed(3) || '0.000'} SOL`,
      subValue: `$${data.treasury_usd?.toFixed(2) || '0.00'}`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: "emerald",
    },
    {
      label: "Total P&L",
      value: `${data.total_pnl_sol >= 0 ? '+' : ''}${data.total_pnl_sol?.toFixed(4) || '0.0000'} SOL`,
      subValue: `${data.total_pnl_pct >= 0 ? '+' : ''}${data.total_pnl_pct?.toFixed(2) || '0.00'}%`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      color: data.total_pnl_sol >= 0 ? "green" : "red",
    },
    {
      label: "Win Rate",
      value: `${data.win_rate?.toFixed(1) || '0.0'}%`,
      subValue: `${data.win_count || 0}W / ${data.loss_count || 0}L`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: data.win_rate >= 50 ? "emerald" : "orange",
    },
    {
      label: "Total Trades",
      value: data.total_trades || 0,
      subValue: `${data.open_positions || 0} open positions`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
      color: "blue",
    },
    {
      label: "Avg Win",
      value: `+${data.avg_win_pct?.toFixed(1) || '0.0'}%`,
      subValue: "per winning trade",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      ),
      color: "green",
    },
    {
      label: "Avg Loss",
      value: `${data.avg_loss_pct?.toFixed(1) || '0.0'}%`,
      subValue: "per losing trade",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      ),
      color: "red",
    },
  ];

  const colorClasses = {
    emerald: "from-emerald-500/20 to-emerald-600/10 text-emerald-400",
    green: "from-green-500/20 to-green-600/10 text-green-400",
    red: "from-red-500/20 to-red-600/10 text-red-400",
    orange: "from-orange-500/20 to-orange-600/10 text-orange-400",
    blue: "from-blue-500/20 to-blue-600/10 text-blue-400",
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4" data-testid="stats-cards">
      {stats.map((stat, index) => (
        <Card 
          key={index} 
          className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors"
        >
          <CardContent className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg bg-gradient-to-br ${colorClasses[stat.color]}`}>
                {stat.icon}
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-zinc-500 uppercase tracking-wider">{stat.label}</p>
              <p className={`text-xl font-bold ${
                stat.color === 'red' ? 'text-red-400' : 
                stat.color === 'green' ? 'text-green-400' : 
                'text-white'
              }`}>
                {stat.value}
              </p>
              <p className="text-xs text-zinc-500">{stat.subValue}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
