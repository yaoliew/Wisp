import { StatsCards } from './StatsCards';
import { CallLogsTable } from './CallLogsTable';

export function Dashboard() {
  return (
    <div className="p-8 space-y-6">
      <StatsCards />
      <CallLogsTable />
    </div>
  );
}
