import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMemo } from "react";

export default function PnLChart({ data }) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Sort by timestamp and prepare data
    return data
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      .map(item => ({
        date: new Date(item.timestamp),
        value: item.treasury_sol,
        usd: item.treasury_usd
      }));
  }, [data]);

  const { minValue, maxValue, valueRange } = useMemo(() => {
    if (chartData.length === 0) return { minValue: 0, maxValue: 1, valueRange: 1 };
    const values = chartData.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    return { minValue: min - range * 0.1, maxValue: max + range * 0.1, valueRange: range * 1.2 };
  }, [chartData]);

  const pathD = useMemo(() => {
    if (chartData.length < 2) return "";
    
    const width = 100;
    const height = 100;
    
    return chartData.map((point, i) => {
      const x = (i / (chartData.length - 1)) * width;
      const y = height - ((point.value - minValue) / valueRange) * height;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  }, [chartData, minValue, valueRange]);

  const areaD = useMemo(() => {
    if (chartData.length < 2) return "";
    return `${pathD} L 100 100 L 0 100 Z`;
  }, [pathD, chartData.length]);

  const startValue = chartData[0]?.value || 0;
  const endValue = chartData[chartData.length - 1]?.value || 0;
  const change = endValue - startValue;
  const changePercent = startValue > 0 ? (change / startValue) * 100 : 0;
  const isPositive = change >= 0;

  return (
    <Card className="bg-zinc-900/50 border-zinc-800" data-testid="pnl-chart">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">Treasury Performance</CardTitle>
          <div className="text-right">
            <p className={`text-lg font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}{change.toFixed(4)} SOL
            </p>
            <p className={`text-sm ${isPositive ? 'text-green-400/70' : 'text-red-400/70'}`}>
              {isPositive ? '+' : ''}{changePercent.toFixed(2)}% (30d)
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length < 2 ? (
          <div className="h-[200px] flex items-center justify-center text-zinc-500">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-2 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p>No treasury data yet</p>
              <p className="text-xs text-zinc-600 mt-1">Data will appear as your bot trades</p>
            </div>
          </div>
        ) : (
          <div className="relative h-[200px]">
            <svg 
              viewBox="0 0 100 100" 
              className="w-full h-full"
              preserveAspectRatio="none"
            >
              {/* Grid lines */}
              <defs>
                <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity="0.3" />
                  <stop offset="100%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity="0" />
                </linearGradient>
              </defs>
              
              {/* Horizontal grid lines */}
              {[0, 25, 50, 75, 100].map(y => (
                <line 
                  key={y}
                  x1="0" 
                  y1={y} 
                  x2="100" 
                  y2={y} 
                  stroke="#27272a" 
                  strokeWidth="0.3"
                />
              ))}
              
              {/* Area fill */}
              <path
                d={areaD}
                fill="url(#chartGradient)"
              />
              
              {/* Line */}
              <path
                d={pathD}
                fill="none"
                stroke={isPositive ? "#10b981" : "#ef4444"}
                strokeWidth="0.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>

            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-zinc-500 -ml-1">
              <span>{maxValue.toFixed(2)}</span>
              <span>{((maxValue + minValue) / 2).toFixed(2)}</span>
              <span>{minValue.toFixed(2)}</span>
            </div>

            {/* X-axis labels */}
            <div className="absolute bottom-0 left-8 right-0 flex justify-between text-xs text-zinc-500 -mb-5">
              <span>{chartData[0]?.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
              <span>{chartData[chartData.length - 1]?.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
