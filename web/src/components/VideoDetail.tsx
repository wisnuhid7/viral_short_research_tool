import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { VideoWithScore, Summary } from 'shared';
import { getSummary, addToCollection, getCollections, createCollection } from '../lib/api';

interface VideoDetailProps {
  video: VideoWithScore;
  onClose: () => void;
}

export function VideoDetail({ video, onClose }: VideoDetailProps) {
  const [showCollectionModal, setShowCollectionModal] = useState(false);

  const { data: summary, isLoading: summaryLoading, error: summaryError, refetch } = useQuery({
    queryKey: ['summary', video.id],
    queryFn: () => getSummary(video.id),
    enabled: false, // only fetch when user clicks
    retry: 1,
  });

  return (
    <div className="animate-fade-in" style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-subtle)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        padding: '20px', borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: '0 0 4px 0' }}>
            {video.title}
          </h2>
          <p style={{ fontSize: '0.813rem', color: 'var(--text-secondary)', margin: 0 }}>
            {video.channelTitle}
            {video.subscriberCount ? ` · ${formatNumber(video.subscriberCount)} subs` : ''}
          </p>
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={onClose}
          aria-label="Tutup detail"
        >
          ✕
        </button>
      </div>

      {/* Video link */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <a
          href={`https://youtube.com/shorts/${video.id}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: 'var(--accent-secondary)', fontSize: '0.813rem',
            textDecoration: 'none',
          }}
        >
          ↗ Tonton di YouTube
        </a>
      </div>

      {/* Stats grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1px',
        background: 'var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)',
      }}>
        <StatBox label="Views" value={formatNumber(video.viewCount)} />
        <StatBox label="Likes" value={formatNumber(video.likeCount)} />
        <StatBox label="Komentar" value={formatNumber(video.commentCount)} />
        <StatBox
          label="Skor Viral"
          value={`${Math.round(video.viralScore.totalScore * 100)}`}
          highlight
        />
      </div>

      {/* Score breakdown */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Komponen skor (sampel: {video.viralScore.sampleSize} video)
          {video.viralScore.confidencePenalty && ' · ⚠ Penalti: video masih baru (\u003c3 jam)'}
        </p>
        <div style={{ display: 'flex', gap: '16px' }}>
          <ScoreDetail label="Velocity" raw={Math.round(video.viralScore.velocity)} norm={video.viralScore.velocityNorm} unit="views/jam" />
          <ScoreDetail label="Reach" raw={video.viralScore.reachRatio.toFixed(1)} norm={video.viralScore.reachRatioNorm} unit="×subs" />
          <ScoreDetail label="Engagement" raw={`${(video.viralScore.engagement * 100).toFixed(2)}%`} norm={video.viralScore.engagementNorm} unit="" />
        </div>
      </div>

      {/* Summary section */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '0.938rem', fontWeight: 600, margin: 0 }}>
            📝 Ringkasan & Analisis Hook
          </h3>
          {!summary && !summaryLoading && (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => { refetch(); }}
            >
              Buat Ringkasan
            </button>
          )}
        </div>

        {summaryLoading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="skeleton" style={{ height: '16px', width: '80%' }} />
            <div className="skeleton" style={{ height: '16px', width: '60%' }} />
            <div className="skeleton" style={{ height: '16px', width: '70%' }} />
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Sedang menganalisis video... (bisa sampai 20 detik)
            </p>
          </div>
        )}

        {summaryError && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)', padding: '12px', fontSize: '0.813rem', color: '#fca5a5',
          }}>
            Gagal membuat ringkasan: {(summaryError as Error).message}
          </div>
        )}

        {summary && <SummaryDisplay summary={summary} />}
      </div>

      {/* Actions */}
      <div style={{
        padding: '16px 20px', display: 'flex', gap: '8px', flexWrap: 'wrap',
      }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setShowCollectionModal(true)}
        >
          📌 Simpan ke Koleksi
        </button>
      </div>

      {/* Collection modal */}
      {showCollectionModal && (
        <CollectionModal
          videoId={video.id}
          onClose={() => setShowCollectionModal(false)}
        />
      )}
    </div>
  );
}

function SummaryDisplay({ summary }: { summary: Summary }) {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {summary.confidence === 'low' && (
        <div className="warning-banner">
          ⚠ Kepercayaan rendah — analisis hanya berdasarkan judul dan deskripsi (transkrip tidak tersedia).
        </div>
      )}

      <div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>Topik</p>
        <p style={{ fontSize: '0.875rem', margin: 0 }}>{summary.topic}</p>
      </div>

      <div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>🎯 Hook (3 detik pertama)</p>
        <p style={{
          fontSize: '0.875rem', margin: 0,
          background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)',
          borderRadius: 'var(--radius-sm)', padding: '10px',
        }}>
          {summary.hookFirst3Seconds}
        </p>
      </div>

      <div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>Struktur</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <StructureStep step="1" label="Hook" text={summary.structure.hook} />
          <StructureStep step="2" label="Isi" text={summary.structure.body} />
          <StructureStep step="3" label="CTA" text={summary.structure.cta} />
        </div>
      </div>

      <div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>Gaya</p>
        <span className="badge" style={{
          background: 'rgba(6,182,212,0.15)', color: 'var(--accent-secondary)',
          border: '1px solid rgba(6,182,212,0.3)',
        }}>
          {summary.style}
        </span>
      </div>

      {summary.keyMoments.length > 0 && (
        <div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>Momen Kunci</p>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.813rem' }}>
            {summary.keyMoments.map((moment, i) => (
              <li key={i} style={{ marginBottom: '2px' }}>{moment}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StructureStep({ step, label, text }: { step: string; label: string; text: string }) {
  return (
    <div style={{
      display: 'flex', gap: '10px', alignItems: 'flex-start', fontSize: '0.813rem',
    }}>
      <span style={{
        background: 'var(--accent-gradient)', color: 'white',
        borderRadius: '50%', width: '22px', height: '22px', minWidth: '22px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.688rem', fontWeight: 700,
      }}>
        {step}
      </span>
      <div>
        <strong style={{ color: 'var(--text-secondary)' }}>{label}:</strong> {text}
      </div>
    </div>
  );
}

function StatBox({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)', padding: '12px', textAlign: 'center',
    }}>
      <p style={{ fontSize: '0.688rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>{label}</p>
      <p style={{
        fontSize: '1.125rem', fontWeight: 700, margin: 0,
        color: highlight ? 'var(--accent-primary)' : undefined,
      }}>
        {value}
      </p>
    </div>
  );
}

function ScoreDetail({ label, raw, norm, unit }: { label: string; raw: string | number; norm: number; unit: string }) {
  const pct = Math.round(norm * 100);
  return (
    <div style={{ flex: 1, textAlign: 'center' }}>
      <p style={{ fontSize: '0.688rem', color: 'var(--text-muted)', margin: '0 0 2px 0' }}>{label}</p>
      <p style={{ fontSize: '0.875rem', fontWeight: 600, margin: '0 0 2px 0' }}>{raw} {unit}</p>
      <p style={{ fontSize: '0.688rem', color: 'var(--text-secondary)', margin: 0 }}>persentil {pct}%</p>
    </div>
  );
}

// ─── Collection Modal ────────────────────────────────────

function CollectionModal({ videoId, onClose }: { videoId: string; onClose: () => void }) {
  const [notes, setNotes] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [newName, setNewName] = useState('');
  const [saving, setSaving] = useState(false);

  const { data: collections, refetch: refetchCollections } = useQuery({
    queryKey: ['collections'],
    queryFn: getCollections,
  });

  async function handleSave(collectionId: number) {
    setSaving(true);
    try {
      const tags = tagsInput.split(',').map((t) => t.trim()).filter(Boolean);
      await addToCollection(collectionId, videoId, tags, notes);
      onClose();
    } catch {
      // Error is shown via UI
    } finally {
      setSaving(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    try {
      await createCollection(newName.trim(), '');
      setNewName('');
      refetchCollections();
    } catch {
      // Error is shown via UI
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 50, backdropFilter: 'blur(4px)',
    }} onClick={onClose}>
      <div
        className="card animate-fade-in"
        style={{ width: '400px', maxHeight: '70vh', overflow: 'auto', padding: '20px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 16px 0' }}>
          📌 Simpan ke Koleksi
        </h3>

        {/* Notes and tags */}
        <div style={{ marginBottom: '12px' }}>
          <label htmlFor="save-tags" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Tag (pisahkan koma)
          </label>
          <input
            id="save-tags"
            className="input"
            placeholder="hook-bagus, referensi-edit"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            style={{ marginTop: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '16px' }}>
          <label htmlFor="save-notes" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Catatan
          </label>
          <textarea
            id="save-notes"
            className="input"
            placeholder="Catatan pribadi tentang video ini..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            style={{ marginTop: '4px', resize: 'vertical' }}
          />
        </div>

        {/* Existing collections */}
        {collections && collections.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Pilih koleksi:
            </p>
            {collections.map((c) => (
              <button
                key={c.id}
                className="btn btn-secondary btn-sm"
                onClick={() => handleSave(c.id)}
                disabled={saving}
                style={{ marginRight: '6px', marginBottom: '6px' }}
              >
                {c.name}
              </button>
            ))}
          </div>
        )}

        {/* Create new */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            className="input"
            placeholder="Nama koleksi baru..."
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            aria-label="Nama koleksi baru"
          />
          <button
            className="btn btn-primary btn-sm"
            onClick={handleCreate}
            disabled={!newName.trim()}
          >
            Buat
          </button>
        </div>
      </div>
    </div>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}
