import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function TradeHistory({ trades }) {
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (mins) => {
    if (mins < 60) return `${Math.round(mins)}m`;
    if (mins < 1440) return `${Math.round(mins / 60)}h`;
    return `${Math.round(mins / 1440)}d`;
  };

  return (
    <Card className="bg-zinc-900/50 border-zinc-800" data-testid="trade-history">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">Trade History</CardTitle>
          <Badge variant="outline" className="border-zinc-600 text-zinc-400">
            {trades.length} trades
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {trades.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <svg className="w-12 h-12 mx-auto mb-2 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <p>No trade history yet</p>
            <p className="text-xs text-zinc-600 mt-1">Completed trades will appear here</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <table className="w-full">
              <thead className="bg-zinc-800/50 sticky top-0">
                <tr className="text-xs text-zinc-400 uppercase">
                  <th className="text-left p-3 font-medium">Token</th>
                  <th className="text-right p-3 font-medium">Entry</th>
                  <th className="text-right p-3 font-medium">Exit</th>
                  <th className="text-right p-3 font-medium">P&L</th>
                  <th className="text-right p-3 font-medium">Duration</th>
                  <th className="text-center p-3 font-medium">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {trades.map((trade, idx) => (
                  <tr key={trade.id || idx} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="p-3">
                      <div>
                        <p className="font-medium text-white">{trade.symbol}</p>
                        <p className="text-xs text-zinc-500">{formatDate(trade.exit_time)}</p>
                      </div>
                    </td>
                    <td className="p-3 text-right">
                      <p className="text-zinc-300">${trade.entry_price?.toFixed(8)}</p>
                      <p className="text-xs text-zinc-500">{trade.cost_sol?.toFixed(4)} SOL</p>
                    </td>
                    <td className="p-3 text-right">
                      <p className="text-zinc-300">${trade.exit_price?.toFixed(8)}</p>
                      <p className="text-xs text-zinc-500">{trade.revenue_sol?.toFixed(4)} SOL</p>
                    </td>
                    <td className="p-3 text-right">
                      <p className={`font-medium ${trade.is_win ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct?.toFixed(2)}%
                      </p>
                      <p className={`text-xs ${trade.is_win ? 'text-green-400/70' : 'text-red-400/70'}`}>
                        {trade.pnl_sol >= 0 ? '+' : ''}{trade.pnl_sol?.toFixed(4)} SOL
                      </p>
                    </td>
                    <td className="p-3 text-right text-zinc-400 text-sm">
                      {formatDuration(trade.hold_duration_mins || 0)}
                    </td>
                    <td className="p-3 text-center">
                      <Badge 
                        className={`${
                          trade.is_win 
                            ? 'bg-green-500/20 text-green-400 border-green-500/30' 
                            : 'bg-red-500/20 text-red-400 border-red-500/30'
                        }`}
                      >
                        {trade.is_win ? 'WIN' : 'LOSS'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
