import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getCollections,
  createCollection,
  getCollectionItems,
  removeFromCollection,
  deleteCollection,
  getSummary,
} from '../lib/api';
import type { Summary } from 'shared';

interface CollectionsViewProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CollectionsView({ isOpen, onClose }: CollectionsViewProps) {
  const queryClient = useQueryClient();
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [activeVideoItem, setActiveVideoItem] = useState<{
    video_id: string;
    video_title: string;
    channel_title: string;
    thumbnail_url: string;
    notes: string;
    tags: string;
    view_count: number;
  } | null>(null);

  // Fetch collections
  const { data: collections = [], isLoading: isCollectionsLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: getCollections,
    enabled: isOpen,
  });

  // Fetch items for selected collection
  const { data: items = [], isLoading: isItemsLoading } = useQuery({
    queryKey: ['collection-items', selectedCollectionId],
    queryFn: () => (selectedCollectionId ? getCollectionItems(selectedCollectionId) : Promise.resolve([])),
    enabled: !!selectedCollectionId && isOpen,
  });

  // Fetch summary for inspected video
  const {
    data: videoSummary,
    isLoading: isSummaryLoading,
    refetch: fetchSummary,
  } = useQuery({
    queryKey: ['summary', activeVideoItem?.video_id],
    queryFn: () => (activeVideoItem ? getSummary(activeVideoItem.video_id) : Promise.reject('No video')),
    enabled: false,
    retry: 1,
  });

  // Create collection mutation
  const createMutation = useMutation({
    mutationFn: () => createCollection(newName.trim(), newDesc.trim()),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setNewName('');
      setNewDesc('');
      setShowCreateForm(false);
      setSelectedCollectionId(res.id);
    },
  });

  // Remove video mutation
  const removeVideoMutation = useMutation({
    mutationFn: ({ collectionId, videoId }: { collectionId: number; videoId: string }) =>
      removeFromCollection(collectionId, videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-items', selectedCollectionId] });
      if (activeVideoItem?.video_id) {
        setActiveVideoItem(null);
      }
    },
  });

  // Delete collection mutation
  const deleteCollectionMutation = useMutation({
    mutationFn: (collectionId: number) => deleteCollection(collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setSelectedCollectionId(null);
    },
  });

  if (!isOpen) return null;

  const activeCollection = collections.find((c) => c.id === selectedCollectionId);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        className="glass animate-fade-in"
        style={{
          width: '100%',
          maxWidth: '1000px',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 'var(--radius-lg)',
          backgroundColor: '#0f172a',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              📁 Koleksi Riset Tersimpan
            </h2>
            <p style={{ fontSize: '0.813rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Kelola video Shorts inspirasi, catatan, dan analisis hook tersimpan
            </p>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.875rem' }}
          >
            ✕ Tutup
          </button>
        </div>

        {/* Content Layout */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Sidebar: List of Collections */}
          <div
            style={{
              width: '260px',
              borderRight: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
            }}
          >
            <div style={{ padding: '14px', borderBottom: '1px solid var(--border-color)' }}>
              {!showCreateForm ? (
                <button
                  className="btn btn-primary"
                  style={{ width: '100%', fontSize: '0.875rem' }}
                  onClick={() => setShowCreateForm(true)}
                >
                  + Buat Koleksi Baru
                </button>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <input
                    type="text"
                    className="input"
                    placeholder="Nama koleksi..."
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    style={{ fontSize: '0.813rem', padding: '6px 10px' }}
                    autoFocus
                  />
                  <input
                    type="text"
                    className="input"
                    placeholder="Deskripsi (opsional)..."
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    style={{ fontSize: '0.813rem', padding: '6px 10px' }}
                  />
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      className="btn btn-primary"
                      style={{ flex: 1, padding: '4px', fontSize: '0.75rem' }}
                      disabled={!newName.trim() || createMutation.isPending}
                      onClick={() => createMutation.mutate()}
                    >
                      Simpan
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                      onClick={() => setShowCreateForm(false)}
                    >
                      Batal
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Collections List */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
              {isCollectionsLoading ? (
                <p style={{ padding: '16px', fontSize: '0.813rem', color: 'var(--text-secondary)' }}>Memuat koleksi...</p>
              ) : collections.length === 0 ? (
                <p style={{ padding: '16px', fontSize: '0.813rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
                  Belum ada koleksi.
                </p>
              ) : (
                collections.map((c) => {
                  const isSelected = c.id === selectedCollectionId;
                  return (
                    <div
                      key={c.id}
                      onClick={() => {
                        setSelectedCollectionId(c.id);
                        setActiveVideoItem(null);
                      }}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-md)',
                        marginBottom: '4px',
                        cursor: 'pointer',
                        backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                        border: isSelected ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.875rem', color: isSelected ? '#60a5fa' : 'var(--text-primary)' }}>
                        {c.name}
                      </div>
                      {c.description && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {c.description}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Main Area: Collection Details & Videos */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: '20px' }}>
            {!selectedCollectionId ? (
              <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>👈</div>
                <p>Pilih salah satu koleksi di sebelah kiri untuk melihat daftar videonya.</p>
              </div>
            ) : (
              <div>
                {/* Collection Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>
                      {activeCollection?.name}
                    </h3>
                    {activeCollection?.description && (
                      <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        {activeCollection.description}
                      </p>
                    )}
                  </div>
                  <button
                    className="btn"
                    style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 12px', fontSize: '0.75rem' }}
                    onClick={() => {
                      if (confirm(`Hapus koleksi "${activeCollection?.name}"?`)) {
                        deleteCollectionMutation.mutate(selectedCollectionId);
                      }
                    }}
                  >
                    Hapus Koleksi
                  </button>
                </div>

                {/* Videos List */}
                {isItemsLoading ? (
                  <p style={{ color: 'var(--text-secondary)' }}>Memuat video...</p>
                ) : items.length === 0 ? (
                  <div style={{ padding: '32px', textAlign: 'center', backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-md)' }}>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                      Belum ada video di koleksi ini.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {items.map((item) => {
                      let parsedTags: string[] = [];
                      try {
                        parsedTags = JSON.parse(item.tags);
                      } catch {
                        parsedTags = [];
                      }

                      const isInspecting = activeVideoItem?.video_id === item.video_id;

                      return (
                        <div
                          key={item.id}
                          className="glass"
                          style={{
                            padding: '14px',
                            borderRadius: 'var(--radius-md)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                            border: isInspecting ? '1px solid #3b82f6' : '1px solid var(--border-color)',
                            backgroundColor: isInspecting ? 'rgba(59, 130, 246, 0.05)' : 'rgba(255,255,255,0.02)',
                          }}
                        >
                          <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
                            <img
                              src={item.thumbnail_url}
                              alt={item.video_title}
                              style={{
                                width: '70px',
                                height: '95px',
                                objectFit: 'cover',
                                borderRadius: 'var(--radius-sm)',
                                flexShrink: 0,
                                cursor: 'pointer',
                              }}
                              onClick={() => {
                                setActiveVideoItem(item);
                                fetchSummary();
                              }}
                            />
                            <div
                              style={{ flex: 1, minWidth: 0, cursor: 'pointer' }}
                              onClick={() => {
                                setActiveVideoItem(item);
                                fetchSummary();
                              }}
                            >
                              <h4
                                style={{
                                  margin: 0,
                                  fontSize: '0.938rem',
                                  fontWeight: 600,
                                  color: isInspecting ? '#60a5fa' : 'var(--text-primary)',
                                }}
                              >
                                {item.video_title}
                              </h4>
                              <p style={{ margin: '4px 0', fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
                                {item.channel_title} • {Number(item.view_count).toLocaleString()} views
                              </p>

                              {item.notes && (
                                <div
                                  style={{
                                    fontSize: '0.75rem',
                                    color: '#cbd5e1',
                                    backgroundColor: 'rgba(255,255,255,0.05)',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    marginTop: '4px',
                                  }}
                                >
                                  📝 {item.notes}
                                </div>
                              )}

                              {parsedTags.length > 0 && (
                                <div style={{ display: 'flex', gap: '4px', marginTop: '6px', flexWrap: 'wrap' }}>
                                  {parsedTags.map((tag) => (
                                    <span
                                      key={tag}
                                      style={{
                                        fontSize: '0.7rem',
                                        backgroundColor: 'rgba(59, 130, 246, 0.15)',
                                        color: '#93c5fd',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                      }}
                                    >
                                      #{tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Action Buttons */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flexShrink: 0 }}>
                              <button
                                className="btn btn-primary"
                                style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                                onClick={() => {
                                  setActiveVideoItem(item);
                                  fetchSummary();
                                }}
                              >
                                {isInspecting ? '🔍 Analisis Aktif' : '🔍 Analisis Hook'}
                              </button>
                              <a
                                href={`https://www.youtube.com/shorts/${item.video_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-secondary"
                                style={{ padding: '6px 12px', fontSize: '0.75rem', textDecoration: 'none', textAlign: 'center' }}
                              >
                                ▶ YouTube
                              </a>
                              <button
                                className="btn"
                                style={{
                                  padding: '4px 8px',
                                  fontSize: '0.7rem',
                                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                  color: '#f87171',
                                  border: '1px solid rgba(239, 68, 68, 0.2)',
                                }}
                                onClick={() =>
                                  removeVideoMutation.mutate({
                                    collectionId: selectedCollectionId,
                                    videoId: item.video_id,
                                  })
                                }
                              >
                                Hapus
                              </button>
                            </div>
                          </div>

                          {/* Expanded Analysis View for this Item */}
                          {isInspecting && (
                            <div
                              style={{
                                borderTop: '1px solid var(--border-color)',
                                paddingTop: '12px',
                                marginTop: '4px',
                              }}
                            >
                              <h5 style={{ margin: '0 0 8px 0', fontSize: '0.875rem', fontWeight: 600, color: '#93c5fd' }}>
                                🧠 Ringkasan & Pola Hook Video
                              </h5>
                              {isSummaryLoading ? (
                                <p style={{ fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
                                  Sedang menganalisis struktur video...
                                </p>
                              ) : videoSummary ? (
                                <SummaryDetails summary={videoSummary} />
                              ) : (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <span style={{ fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
                                    Ringkasan AI belum dibuat untuk video ini.
                                  </span>
                                  <button
                                    className="btn btn-primary"
                                    style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                                    onClick={() => fetchSummary()}
                                  >
                                    Buat Analisis AI Sekarang
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryDetails({ summary }: { summary: Summary }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.813rem' }}>
      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '4px' }}>
        <strong style={{ color: '#60a5fa' }}>🎯 Hook (3 Detik Pertama):</strong> {summary.hookFirst3Seconds}
      </div>
      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '4px' }}>
        <strong style={{ color: '#34d399' }}>🏗️ Struktur:</strong>
        <div style={{ marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span>• <b>Hook:</b> {summary.structure.hook}</span>
          <span>• <b>Body:</b> {summary.structure.body}</span>
          <span>• <b>CTA:</b> {summary.structure.cta}</span>
        </div>
      </div>
      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '4px' }}>
        <strong style={{ color: '#fbbf24' }}>🎨 Gaya:</strong> {summary.style}
      </div>
    </div>
  );
}
