import type { VideoWithScore } from 'shared';

interface VideoCardProps {
  video: VideoWithScore;
  onSelect: (video: VideoWithScore) => void;
  isSelected: boolean;
}

export function VideoCard({ video, onSelect, isSelected }: VideoCardProps) {
  const score = video.viralScore;
  const scorePercent = Math.round(score.totalScore * 100);
  const scoreClass = scorePercent >= 70 ? 'high' : scorePercent >= 40 ? 'medium' : 'low';

  const hoursAgo = Math.round(
    (Date.now() - new Date(video.publishedAt).getTime()) / (1000 * 60 * 60)
  );
  const timeAgo = hoursAgo < 24
    ? `${hoursAgo} jam lalu`
    : `${Math.round(hoursAgo / 24)} hari lalu`;

  return (
    <div
      className="card animate-fade-in"
      onClick={() => onSelect(video)}
      role="button"
      tabIndex={0}
      aria-label={`Video: ${video.title}`}
      onKeyDown={(e) => { if (e.key === 'Enter') onSelect(video); }}
      style={{
        cursor: 'pointer',
        padding: '0',
        overflow: 'hidden',
        borderColor: isSelected ? 'var(--accent-primary)' : undefined,
        boxShadow: isSelected ? 'var(--shadow-glow)' : undefined,
      }}
    >
      {/* Thumbnail */}
      <div style={{ position: 'relative', aspectRatio: '16/9', overflow: 'hidden' }}>
        <img
          src={video.thumbnailUrl}
          alt={video.title}
          loading="lazy"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />

        {/* Viral score badge */}
        <div
          className={`score-bg-${scoreClass}`}
          style={{
            position: 'absolute', top: '8px', right: '8px',
            borderRadius: '8px', padding: '4px 10px',
            fontSize: '0.813rem', fontWeight: 700,
            display: 'flex', alignItems: 'center', gap: '4px',
          }}
        >
          <span className={`score-${scoreClass}`}>🔥 {scorePercent}</span>
        </div>

        {/* Duration badge */}
        <div style={{
          position: 'absolute', bottom: '8px', right: '8px',
          background: 'rgba(0,0,0,0.75)', borderRadius: '4px',
          padding: '2px 6px', fontSize: '0.75rem',
        }}>
          {video.duration}s
        </div>

        {/* Confidence penalty indicator */}
        {score.confidencePenalty && (
          <div style={{
            position: 'absolute', top: '8px', left: '8px',
            background: 'rgba(234,179,8,0.9)', borderRadius: '4px',
            padding: '2px 6px', fontSize: '0.688rem', color: '#000', fontWeight: 600,
          }}>
            ⚠ Baru
          </div>
        )}
      </div>

      {/* Info */}
      <div style={{ padding: '12px 14px' }}>
        <h3 style={{
          fontSize: '0.875rem', fontWeight: 600, lineHeight: 1.4,
          margin: '0 0 6px 0',
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}>
          {video.title}
        </h3>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 8px 0' }}>
          {video.channelTitle} · {timeAgo}
        </p>

        {/* Stats row */}
        <div style={{
          display: 'flex', gap: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)',
        }}>
          <span title="Views">👁 {formatNumber(video.viewCount)}</span>
          <span title="Likes">❤️ {formatNumber(video.likeCount)}</span>
          <span title="Komentar">💬 {formatNumber(video.commentCount)}</span>
        </div>

        {/* Score breakdown (compact) */}
        <div style={{
          display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap',
        }}>
          <MiniBar label="Velocity" value={score.velocityNorm} />
          <MiniBar label="Reach" value={score.reachRatioNorm} />
          <MiniBar label="Engage" value={score.engagementNorm} />
        </div>
      </div>
    </div>
  );
}

function MiniBar({ label, value }: { label: string; value: number }) {
  const percent = Math.round(value * 100);
  const color = percent >= 70 ? 'var(--score-high)' : percent >= 40 ? 'var(--score-medium)' : 'var(--score-low)';

  return (
    <div style={{ flex: 1, minWidth: '60px' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '0.625rem', color: 'var(--text-muted)', marginBottom: '2px',
      }}>
        <span>{label}</span>
        <span>{percent}%</span>
      </div>
      <div style={{
        height: '3px', background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${percent}%`, background: color,
          borderRadius: '2px', transition: 'width 0.5s ease',
        }} />
      </div>
    </div>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}
