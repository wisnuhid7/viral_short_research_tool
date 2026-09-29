import { useQuery } from '@tanstack/react-query';
import { getQuota } from '../lib/api';

export function QuotaIndicator() {
  const { data: quota } = useQuery({
    queryKey: ['quota'],
    queryFn: getQuota,
    refetchInterval: 60000, // refresh every minute
  });

  if (!quota) return null;

  const usedPercent = Math.round((quota.used / quota.limit) * 100);
  const barColor =
    usedPercent >= 90 ? 'var(--score-low)' :
    usedPercent >= 70 ? 'var(--score-medium)' :
    'var(--score-high)';

  const resetTime = new Date(quota.resetsAt).toLocaleString('id-ID', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '10px',
      fontSize: '0.75rem', color: 'var(--text-secondary)',
    }}>
      <span>YouTube API</span>
      <div style={{
        width: '80px', height: '4px',
        background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden',
      }}>
        <div style={{
          width: `${usedPercent}%`, height: '100%',
          background: barColor, borderRadius: '2px',
          transition: 'width 0.3s ease',
        }} />
      </div>
      <span>
        {quota.remaining.toLocaleString('id-ID')}/{quota.limit.toLocaleString('id-ID')}
      </span>
      <span style={{ color: 'var(--text-muted)' }}>
        Reset {resetTime}
      </span>
    </div>
  );
}
