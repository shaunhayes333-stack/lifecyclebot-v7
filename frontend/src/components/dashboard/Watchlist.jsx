import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function Watchlist({ tokens }) {
  const formatNumber = (num, decimals = 2) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(decimals)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(decimals)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };

  return (
    <Card className="bg-zinc-900/50 border-zinc-800" data-testid="watchlist">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">Watchlist</CardTitle>
          <Badge variant="outline" className="border-blue-500/50 text-blue-400">
            {tokens.length} tokens
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {tokens.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <svg className="w-12 h-12 mx-auto mb-2 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <p>No tokens in watchlist</p>
            <p className="text-xs text-zinc-600 mt-1">Scanned tokens will appear here</p>
          </div>
        ) : (
          <ScrollArea className="h-[300px]">
            <table className="w-full">
              <thead className="bg-zinc-800/50 sticky top-0">
                <tr className="text-xs text-zinc-400 uppercase">
                  <th className="text-left p-3 font-medium">Token</th>
                  <th className="text-right p-3 font-medium">Price</th>
                  <th className="text-right p-3 font-medium">1H</th>
                  <th className="text-right p-3 font-medium">Signal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {tokens.map((token, idx) => {
                  const change = token.price_change_1h || 0;
                  const isUp = change >= 0;
                  
                  return (
                    <tr key={token.mint || idx} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="p-3">
                        <div>
                          <p className="font-medium text-white">{token.symbol}</p>
                          <p className="text-xs text-zinc-500">
                            ${formatNumber(token.liquidity_usd || 0)} liq
                          </p>
                        </div>
                      </td>
                      <td className="p-3 text-right">
                        <p className="text-zinc-300">${token.current_price?.toFixed(8)}</p>
                        <p className="text-xs text-zinc-500">
                          Vol: ${formatNumber(token.volume_24h || 0)}
                        </p>
                      </td>
                      <td className="p-3 text-right">
                        <p className={`font-medium ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                          {isUp ? '+' : ''}{change.toFixed(1)}%
                        </p>
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex flex-col items-end gap-1">
                          <Badge 
                            variant="outline"
                            className={`text-xs ${
                              token.signal === 'BUY' ? 'border-green-500/50 text-green-400' :
                              token.signal === 'SELL' ? 'border-red-500/50 text-red-400' :
                              'border-zinc-600 text-zinc-400'
                            }`}
                          >
                            {token.signal || 'WAIT'}
                          </Badge>
                          <span className="text-xs text-zinc-500">
                            E:{token.entry_score?.toFixed(0) || 0}
                          </span>
                        </div>
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
