import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function PositionsTable({ positions }) {
  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <Card className="bg-zinc-900/50 border-zinc-800" data-testid="positions-table">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">Open Positions</CardTitle>
          <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
            {positions.length} active
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {positions.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <svg className="w-12 h-12 mx-auto mb-2 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p>No open positions</p>
            <p className="text-xs text-zinc-600 mt-1">Positions will appear here when active</p>
          </div>
        ) : (
          <ScrollArea className="h-[300px]">
            <table className="w-full">
              <thead className="bg-zinc-800/50 sticky top-0">
                <tr className="text-xs text-zinc-400 uppercase">
                  <th className="text-left p-3 font-medium">Token</th>
                  <th className="text-right p-3 font-medium">Entry</th>
                  <th className="text-right p-3 font-medium">Current</th>
                  <th className="text-right p-3 font-medium">P&L</th>
                  <th className="text-right p-3 font-medium">Signal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {positions.map((pos, idx) => {
                  const pnlPct = pos.unrealized_pnl_pct || 0;
                  const isProfit = pnlPct >= 0;
                  
                  return (
                    <tr key={pos.id || idx} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="p-3">
                        <div>
                          <p className="font-medium text-white">{pos.symbol}</p>
                          <p className="text-xs text-zinc-500">{formatTime(pos.entry_time)}</p>
                        </div>
                      </td>
                      <td className="p-3 text-right">
                        <p className="text-zinc-300">${pos.entry_price?.toFixed(8)}</p>
                        <p className="text-xs text-zinc-500">{pos.cost_sol?.toFixed(4)} SOL</p>
                      </td>
                      <td className="p-3 text-right">
                        <p className="text-zinc-300">${pos.current_price?.toFixed(8)}</p>
                        <p className="text-xs text-zinc-500">{pos.current_value_sol?.toFixed(4)} SOL</p>
                      </td>
                      <td className="p-3 text-right">
                        <p className={`font-medium ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
                          {isProfit ? '+' : ''}{pnlPct.toFixed(2)}%
                        </p>
                      </td>
                      <td className="p-3 text-right">
                        <Badge 
                          variant="outline"
                          className={`text-xs ${
                            pos.signal === 'BUY' ? 'border-green-500/50 text-green-400' :
                            pos.signal === 'SELL' ? 'border-red-500/50 text-red-400' :
                            pos.signal === 'EXIT' ? 'border-orange-500/50 text-orange-400' :
                            'border-zinc-600 text-zinc-400'
                          }`}
                        >
                          {pos.signal || 'WAIT'}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
