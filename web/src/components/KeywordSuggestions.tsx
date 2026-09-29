import type { KeywordSuggestion } from 'shared';

interface KeywordSuggestionsProps {
  suggestions: KeywordSuggestion[];
  onKeywordClick: (keyword: string) => void;
}

export function KeywordSuggestions({ suggestions, onKeywordClick }: KeywordSuggestionsProps) {
  if (suggestions.length === 0) return null;

  const tagSuggestions = suggestions.filter((s) => s.source === 'tag');
  const titleSuggestions = suggestions.filter((s) => s.source === 'title_word');

  return (
    <div className="card animate-fade-in" style={{ padding: '16px' }}>
      <h3 style={{ fontSize: '0.875rem', fontWeight: 600, margin: '0 0 12px 0' }}>
        💡 Saran Keyword Turunan
      </h3>

      {tagSuggestions.length > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <p style={{ fontSize: '0.688rem', color: 'var(--text-muted)', margin: '0 0 6px 0' }}>
            Dari tag video
          </p>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {tagSuggestions.slice(0, 15).map((s) => (
              <button
                key={`tag-${s.keyword}`}
                className="badge"
                onClick={() => onKeywordClick(s.keyword)}
                style={{
                  cursor: 'pointer', border: '1px solid var(--border-accent)',
                  background: 'rgba(139,92,246,0.1)', color: 'var(--accent-primary)',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  (e.target as HTMLElement).style.background = 'rgba(139,92,246,0.25)';
                }}
                onMouseLeave={(e) => {
                  (e.target as HTMLElement).style.background = 'rgba(139,92,246,0.1)';
                }}
              >
                {s.keyword}
                <span style={{ opacity: 0.6, marginLeft: '4px', fontSize: '0.625rem' }}>
                  ×{s.frequency}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {titleSuggestions.length > 0 && (
        <div>
          <p style={{ fontSize: '0.688rem', color: 'var(--text-muted)', margin: '0 0 6px 0' }}>
            Dari kata di judul
          </p>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {titleSuggestions.slice(0, 15).map((s) => (
              <button
                key={`title-${s.keyword}`}
                className="badge"
                onClick={() => onKeywordClick(s.keyword)}
                style={{
                  cursor: 'pointer', border: '1px solid rgba(6,182,212,0.3)',
                  background: 'rgba(6,182,212,0.1)', color: 'var(--accent-secondary)',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  (e.target as HTMLElement).style.background = 'rgba(6,182,212,0.25)';
                }}
                onMouseLeave={(e) => {
                  (e.target as HTMLElement).style.background = 'rgba(6,182,212,0.1)';
                }}
              >
                {s.keyword}
                <span style={{ opacity: 0.6, marginLeft: '4px', fontSize: '0.625rem' }}>
                  ×{s.frequency}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
