import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface CallsBarChartProps {
  data: Array<{ date: string; count: number }>;
}

export function CallsBarChart({ data }: CallsBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis 
          dataKey="date" 
          stroke="#71717a"
          style={{ fontSize: '12px' }}
        />
        <YAxis 
          stroke="#71717a"
          style={{ fontSize: '12px' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#09090b',
            border: '1px solid #27272a',
            borderRadius: '6px',
            color: '#ffffff'
          }}
          labelStyle={{ color: '#a1a1aa' }}
        />
        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
