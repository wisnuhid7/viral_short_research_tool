import { useState, type FormEvent } from 'react';
import type { TimeRange } from 'shared';

interface SearchBarProps {
  onSearch: (keyword: string, timeRange: TimeRange, language: string, maxDuration: number, minViews: number) => void;
  isLoading: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [keyword, setKeyword] = useState('');
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const [language, setLanguage] = useState('any');
  const [maxDuration, setMaxDuration] = useState(60);
  const [minViews, setMinViews] = useState(5000);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (keyword.trim()) {
      onSearch(keyword.trim(), timeRange, language, maxDuration, minViews);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="animate-fade-in">
      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: '24px' }}>
        {/* Main search input */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              id="search-keyword"
              type="text"
              className="input"
              placeholder="Cari keyword Shorts viral... (contoh: mukbang, tutorial makeup)"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              aria-label="Kata kunci pencarian"
              style={{ paddingLeft: '44px', fontSize: '1rem', height: '48px' }}
            />
            <span style={{
              position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)',
              fontSize: '1.1rem', opacity: 0.5,
            }}>🔍</span>
          </div>
          <button
            id="search-submit"
            type="submit"
            className="btn btn-primary"
            disabled={isLoading || !keyword.trim()}
            style={{ height: '48px', minWidth: '120px' }}
          >
            {isLoading ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="spinner" /> Mencari...
              </span>
            ) : (
              'Cari Shorts'
            )}
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label htmlFor="filter-time" style={{ fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
              Rentang waktu
            </label>
            <select
              id="filter-time"
              className="select"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as TimeRange)}
            >
              <option value="24h">24 jam terakhir</option>
              <option value="7d">7 hari terakhir</option>
              <option value="30d">30 hari terakhir</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label htmlFor="filter-views" style={{ fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
              Min. Penonton
            </label>
            <select
              id="filter-views"
              className="select"
              value={minViews}
              onChange={(e) => setMinViews(Number(e.target.value))}
            >
              <option value={0}>Semua Views</option>
              <option value={5000}>≥ 5.000 (5K)</option>
              <option value={10000}>≥ 10.000 (10K)</option>
              <option value={50000}>≥ 50.000 (50K)</option>
              <option value={100000}>≥ 100.000 (100K)</option>
              <option value={500000}>≥ 500.000 (500K)</option>
              <option value={1000000}>≥ 1.000.000 (1M)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label htmlFor="filter-lang" style={{ fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
              Bahasa
            </label>
            <select
              id="filter-lang"
              className="select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="any">Semua</option>
              <option value="id">Indonesia</option>
              <option value="en">Inggris</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label htmlFor="filter-duration" style={{ fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
              Maks. durasi
            </label>
            <select
              id="filter-duration"
              className="select"
              value={maxDuration}
              onChange={(e) => setMaxDuration(Number(e.target.value))}
            >
              <option value={30}>30 detik</option>
              <option value={60}>60 detik</option>
              <option value={90}>90 detik</option>
              <option value={120}>2 menit</option>
              <option value={180}>3 menit</option>
            </select>
          </div>
        </div>
      </div>
    </form>
  );
}
