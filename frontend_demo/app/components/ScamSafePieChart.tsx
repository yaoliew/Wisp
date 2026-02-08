import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface ScamSafePieChartProps {
  data: {
    scam: number;
    safe: number;
  };
}

const COLORS = ['#ef4444', '#10b981'];

export function ScamSafePieChart({ data }: ScamSafePieChartProps) {
  const chartData = [
    { name: 'Scam', value: data.scam },
    { name: 'Safe', value: data.safe },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: '#09090b',
            border: '1px solid #27272a',
            borderRadius: '6px',
            color: '#ffffff'
          }}
        />
        <Legend 
          wrapperStyle={{ color: '#a1a1aa' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
