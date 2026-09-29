import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { VideoWithScore, SearchResponse, TimeRange } from 'shared';
import { searchVideos, exportVideos, getSearchHistory } from './lib/api';
import { SearchBar } from './components/SearchBar';
import { VideoCard } from './components/VideoCard';
import { VideoDetail } from './components/VideoDetail';
import { KeywordSuggestions } from './components/KeywordSuggestions';
import { QuotaIndicator } from './components/QuotaIndicator';
import { CollectionsView } from './components/CollectionsView';

export default function App() {
  const queryClient = useQueryClient();
  const [selectedVideo, setSelectedVideo] = useState<VideoWithScore | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [currentKeyword, setCurrentKeyword] = useState('');
  const [isCollectionsOpen, setIsCollectionsOpen] = useState(false);

  // Search history query
  const { data: searchHistory = [] } = useQuery({
    queryKey: ['search-history'],
    queryFn: getSearchHistory,
  });

  const searchMutation = useMutation({
    mutationFn: (params: { keyword: string; timeRange: TimeRange; language: string; maxDuration: number; minViews?: number }) =>
      searchVideos(params),
    onSuccess: (data) => {
      setSearchResult(data);
      setSelectedVideo(null);
      queryClient.invalidateQueries({ queryKey: ['search-history'] });
    },
  });

  const handleSearch = useCallback(
    (keyword: string, timeRange: TimeRange, language: string, maxDuration: number, minViews: number) => {
      setCurrentKeyword(keyword);
      searchMutation.mutate({ keyword, timeRange, language, maxDuration, minViews });
    },
    [searchMutation],
  );

  const handleKeywordClick = useCallback(
    (keyword: string) => {
      setCurrentKeyword(keyword);
      searchMutation.mutate({ keyword, timeRange: '7d', language: 'any', maxDuration: 60, minViews: 5000 });
    },
    [searchMutation],
  );

  async function handleExport(format: 'csv' | 'markdown') {
    if (!searchResult || searchResult.videos.length === 0) return;
    try {
      const blob = await exportVideos(
        searchResult.videos.map((v) => v.id),
        format,
        true,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `shorts_research.${format === 'csv' ? 'csv' : 'md'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently handle
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '12px 24px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0 }}>
            <span className="gradient-text">🔥 Viral Shorts</span>
            <span style={{ fontWeight: 500, color: 'var(--text-secondary)', marginLeft: '6px' }}>Research</span>
          </h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.813rem', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
            onClick={() => setIsCollectionsOpen(true)}
          >
            📁 Koleksi Saya
          </button>
          <QuotaIndicator />
        </div>
      </header>

      {/* Collections Modal */}
      <CollectionsView
        isOpen={isCollectionsOpen}
        onClose={() => setIsCollectionsOpen(false)}
      />

      {/* Warning banner */}
      <div style={{ padding: '8px 24px', background: 'var(--bg-primary)' }}>
        <div className="warning-banner">
          ⚠ Gunakan hanya sebagai referensi riset pola dan strategi. Klip untuk Whop harus dari footage resmi campaign.
        </div>
      </div>

      {/* Main content */}
      <main style={{ flex: 1, padding: '16px 24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {/* Search */}
        <div style={{ marginBottom: '20px' }}>
          <SearchBar onSearch={handleSearch} isLoading={searchMutation.isPending} />

          {/* Research History Badges */}
          {searchHistory.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                🕒 Riwayat Riset:
              </span>
              {searchHistory.map((h) => (
                <button
                  key={h.keyword}
                  onClick={() => handleKeywordClick(h.keyword)}
                  className="btn"
                  style={{
                    fontSize: '0.75rem',
                    padding: '3px 10px',
                    borderRadius: '12px',
                    backgroundColor: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#60a5fa';
                    e.currentTarget.style.borderColor = '#3b82f6';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = 'var(--text-secondary)';
                    e.currentTarget.style.borderColor = 'var(--border-color)';
                  }}
                >
                  {h.keyword} <span style={{ opacity: 0.5, fontSize: '0.7rem' }}>({h.resultCount})</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Error state */}
        {searchMutation.isError && (
          <div className="animate-fade-in" style={{
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 'var(--radius-sm)', padding: '16px', marginBottom: '20px',
            color: '#fca5a5', fontSize: '0.875rem',
          }}>
            ❌ {(searchMutation.error as Error).message}
          </div>
        )}

        {/* Results */}
        {searchResult && (
          <div className="animate-fade-in">
            {/* Results header */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              marginBottom: '16px',
            }}>
              <div>
                <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 4px 0' }}>
                  Hasil untuk "<span className="gradient-text">{currentKeyword}</span>"
                </h2>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                  {searchResult.videos.length} video ditemukan
                  {searchResult.cachedAt && ' · 📦 Dari cache'}
                </p>
              </div>

              {searchResult.videos.length > 0 && (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => handleExport('csv')}>
                    📊 CSV
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => handleExport('markdown')}>
                    📝 Markdown
                  </button>
                </div>
              )}
            </div>

            {/* Keyword suggestions */}
            {searchResult.suggestions.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <KeywordSuggestions
                  suggestions={searchResult.suggestions}
                  onKeywordClick={handleKeywordClick}
                />
              </div>
            )}

            {/* Empty state */}
            {searchResult.videos.length === 0 && (
              <div style={{
                textAlign: 'center', padding: '60px 20px',
                color: 'var(--text-muted)',
              }}>
                <p style={{ fontSize: '2rem', margin: '0 0 8px 0' }}>🔍</p>
                <p style={{ fontSize: '1rem', fontWeight: 500 }}>Tidak ada Shorts ditemukan</p>
                <p style={{ fontSize: '0.813rem' }}>Coba keyword lain atau perluas rentang waktu.</p>
              </div>
            )}

            {/* Video grid + detail panel */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: selectedVideo ? '1fr 420px' : '1fr',
              gap: '20px',
              alignItems: 'start',
            }}>
              {/* Video grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                gap: '14px',
              }}>
                {searchResult.videos.map((video) => (
                  <VideoCard
                    key={video.id}
                    video={video}
                    onSelect={setSelectedVideo}
                    isSelected={selectedVideo?.id === video.id}
                  />
                ))}
              </div>

              {/* Detail panel (sticky sidebar) */}
              {selectedVideo && (
                <div style={{ position: 'sticky', top: '16px' }}>
                  <VideoDetail
                    video={selectedVideo}
                    onClose={() => setSelectedVideo(null)}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Initial state */}
        {!searchResult && !searchMutation.isPending && (
          <div style={{
            textAlign: 'center', padding: '80px 20px',
            color: 'var(--text-muted)',
          }}>
            <p style={{ fontSize: '3rem', margin: '0 0 12px 0' }}>🎬</p>
            <h2 style={{
              fontSize: '1.5rem', fontWeight: 700, margin: '0 0 8px 0',
              color: 'var(--text-primary)',
            }}>
              <span className="gradient-text">Riset Shorts Viral</span>
            </h2>
            <p style={{ fontSize: '0.938rem', maxWidth: '500px', margin: '0 auto' }}>
              Masukkan keyword untuk menemukan YouTube Shorts yang sedang viral.
              Analisis skor viralitas, hook, dan pola struktur untuk referensi strategi konten.
            </p>
          </div>
        )}

        {/* Loading skeletons */}
        {searchMutation.isPending && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: '14px', marginTop: '20px',
          }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="card" style={{ overflow: 'hidden' }}>
                <div className="skeleton" style={{ aspectRatio: '16/9' }} />
                <div style={{ padding: '12px 14px' }}>
                  <div className="skeleton" style={{ height: '14px', width: '90%', marginBottom: '8px' }} />
                  <div className="skeleton" style={{ height: '12px', width: '60%', marginBottom: '10px' }} />
                  <div className="skeleton" style={{ height: '10px', width: '80%' }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '12px 24px', textAlign: 'center',
        fontSize: '0.75rem', color: 'var(--text-muted)',
      }}>
        Viral Shorts Research Tool — Data dari YouTube API · Pemakaian pribadi
      </footer>
    </div>
  );
}
