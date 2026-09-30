import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCampaigns, createCampaign, deleteCampaign, syncWhopCampaigns, getWhopSyncStatus } from '../lib/api';
import type { CampaignCategory, CreateCampaignRequest } from 'shared';

interface CampaignRatingViewProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectKeywordForResearch: (keyword: string) => void;
}

const CATEGORIES: { id: CampaignCategory; label: string; icon: string }[] = [
  { id: 'all', label: 'Semua Kategori', icon: '🌟' },
  { id: 'ai_tech', label: 'AI & Tech', icon: '🤖' },
  { id: 'finance_crypto', label: 'Finance & Crypto', icon: '📈' },
  { id: 'business_sidehustle', label: 'Business & Side Hustle', icon: '💼' },
  { id: 'gaming', label: 'Gaming', icon: '🎮' },
  { id: 'fitness_lifestyle', label: 'Fitness & Lifestyle', icon: '🏋️' },
  { id: 'entertainment', label: 'Entertainment', icon: '🎭' },
  { id: 'other', label: 'Lainnya', icon: '📦' },
];

export function CampaignRatingView({ isOpen, onClose, onSelectKeywordForResearch }: CampaignRatingViewProps) {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<CampaignCategory>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [onlyWhopLive, setOnlyWhopLive] = useState(false);
  const [syncNotification, setSyncNotification] = useState<string | null>(null);
  
  // Target Earnings Goal (USD)
  const [targetGoalUSD, setTargetGoalUSD] = useState<number>(50);
  
  // Sort By: 'ease' (Paling Mudah Capai Target), 'rate' (Rate Tertinggi), 'budget' (Budget Terbanyak), 'views' (Views Terendah)
  const [sortBy, setSortBy] = useState<'ease' | 'rate' | 'budget' | 'views'>('ease');
  const [searchQuery, setSearchQuery] = useState('');

  // Form states
  const [formName, setFormName] = useState('');
  const [formBrand, setFormBrand] = useState('');
  const [formCategory, setFormCategory] = useState<CampaignCategory>('ai_tech');
  const [formUrl, setFormUrl] = useState('');
  const [formRate, setFormRate] = useState<number>(4.0);
  const [formTotalBudget, setFormTotalBudget] = useState<number>(5000);
  const [formRemainingBudget, setFormRemainingBudget] = useState<number>(4000);
  const [formKeywords, setFormKeywords] = useState('');
  const [formHashtags, setFormHashtags] = useState('');
  const [formNotes, setFormNotes] = useState('');

  // Fetch campaigns
  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ['campaigns', selectedCategory],
    queryFn: () => getCampaigns(selectedCategory),
    enabled: isOpen,
  });

  // Whop Sync Status Query
  const { data: syncStatus, refetch: refetchSyncStatus } = useQuery({
    queryKey: ['whopSyncStatus'],
    queryFn: getWhopSyncStatus,
    enabled: isOpen,
    refetchInterval: 15000,
  });

  // Whop Sync Mutation
  const syncMutation = useMutation({
    mutationFn: syncWhopCampaigns,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      refetchSyncStatus();
      setSyncNotification(res.message || 'Sinkronisasi Whop MCP selesai!');
      setTimeout(() => setSyncNotification(null), 5000);
    },
    onError: (err: any) => {
      setSyncNotification(`Sinkronisasi Whop gagal: ${err.message || 'Error tidak diketahui'}`);
      setTimeout(() => setSyncNotification(null), 6000);
    },
  });

  // Create campaign mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateCampaignRequest) => createCampaign(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setShowAddForm(false);
      resetForm();
    },
  });

  // Delete campaign mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCampaign(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  function resetForm() {
    setFormName('');
    setFormBrand('');
    setFormCategory('ai_tech');
    setFormUrl('');
    setFormRate(4.0);
    setFormTotalBudget(5000);
    setFormRemainingBudget(4000);
    setFormKeywords('');
    setFormHashtags('');
    setFormNotes('');
  }

  function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim() || !formBrand.trim()) return;

    createMutation.mutate({
      name: formName.trim(),
      creatorOrBrand: formBrand.trim(),
      category: formCategory,
      url: formUrl.trim(),
      ratePerKViews: Number(formRate),
      totalBudget: Number(formTotalBudget),
      remainingBudget: Number(formRemainingBudget),
      targetKeywords: formKeywords.split(',').map((k) => k.trim()).filter(Boolean),
      requiredHashtags: formHashtags.split(',').map((h) => h.trim()).filter(Boolean),
      requiredMentions: [],
      allowedPlatforms: ['YouTube Shorts'],
      notes: formNotes.trim(),
    });
  }

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(10px)',
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
          maxWidth: '1100px',
          maxHeight: '90vh',
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
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'rgba(30, 41, 59, 0.5)',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              🎯 Panduan Memilih Campaign: Paling Mudah Capai Target
            </h2>
            <p style={{ fontSize: '0.813rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Bantu Anda memilih campaign Whop Content Rewards yang paling realistis menghasilkan uang dengan kebutuhan views terendah & potensi viral tertinggi di YouTube Shorts.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px', flexWrap: 'wrap' }}>
              <span style={{
                fontSize: '0.75rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '2px 8px',
                borderRadius: '12px',
                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                color: '#4ade80',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                fontWeight: 600,
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#22c55e', display: 'inline-block', boxShadow: '0 0 6px #22c55e' }}></span>
                Whop MCP: {campaigns.filter((c) => c.isWhopLive || c.id.startsWith('bnty_')).length} Campaign Live
              </span>
              {syncStatus?.lastSyncedAt && (
                <span style={{ fontSize: '0.688rem', color: 'var(--text-muted)' }}>
                  Update: {new Date(syncStatus.lastSyncedAt).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              className="btn btn-secondary"
              style={{
                fontSize: '0.813rem',
                padding: '6px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                borderColor: '#38bdf8',
                color: '#38bdf8',
                backgroundColor: 'rgba(56, 189, 248, 0.08)',
                cursor: (syncMutation.isPending || syncStatus?.status === 'syncing') ? 'not-allowed' : 'pointer',
              }}
              disabled={syncMutation.isPending || syncStatus?.status === 'syncing'}
              onClick={() => syncMutation.mutate()}
              title="Sinkronkan data bounty & campaign langsung secara real-time via Whop MCP"
            >
              <span style={{ display: 'inline-block', animation: (syncMutation.isPending || syncStatus?.status === 'syncing') ? 'spin 1s linear infinite' : 'none' }}>
                🔄
              </span>
              {syncMutation.isPending || syncStatus?.status === 'syncing' ? 'Menyinkronkan MCP...' : 'Sync Whop MCP'}
            </button>
            <button
              className="btn btn-primary"
              style={{ fontSize: '0.813rem', padding: '6px 14px' }}
              onClick={() => setShowAddForm(!showAddForm)}
            >
              {showAddForm ? '✕ Tutup Form' : '+ Tambah Campaign'}
            </button>
            <button
              onClick={onClose}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.875rem' }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Sync Notification Banner */}
        {syncNotification && (
          <div
            style={{
              padding: '8px 24px',
              backgroundColor: syncNotification.includes('gagal') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
              borderBottom: '1px solid var(--border-color)',
              color: syncNotification.includes('gagal') ? '#fca5a5' : '#86efac',
              fontSize: '0.813rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>{syncNotification.includes('gagal') ? '⚠️' : '✓'} {syncNotification}</span>
            <button
              onClick={() => setSyncNotification(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '0.875rem' }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Add Campaign Form Drawer */}
        {showAddForm && (
          <form
            onSubmit={handleCreateSubmit}
            style={{
              padding: '16px 24px',
              borderBottom: '1px solid var(--border-color)',
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px',
            }}
          >
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Nama Campaign</label>
              <input
                type="text"
                className="input"
                placeholder="Contoh: AI Tools Clipping Challenge"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Creator / Brand Whop</label>
              <input
                type="text"
                className="input"
                placeholder="Contoh: NextGen AI Lab"
                value={formBrand}
                onChange={(e) => setFormBrand(e.target.value)}
                required
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Kategori Niche</label>
              <select
                className="select"
                value={formCategory}
                onChange={(e) => setFormCategory(e.target.value as CampaignCategory)}
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              >
                {CATEGORIES.filter((c) => c.id !== 'all').map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.icon} {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Rate ($ per 1.000 Views)</label>
              <input
                type="number"
                step="0.1"
                min="0.5"
                className="input"
                value={formRate}
                onChange={(e) => setFormRate(Number(e.target.value))}
                required
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Budget ($)</label>
              <input
                type="number"
                className="input"
                value={formTotalBudget}
                onChange={(e) => setFormTotalBudget(Number(e.target.value))}
                required
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Sisa Budget Saat Ini ($)</label>
              <input
                type="number"
                className="input"
                value={formRemainingBudget}
                onChange={(e) => setFormRemainingBudget(Number(e.target.value))}
                required
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Link / URL Campaign Whop</label>
              <input
                type="url"
                className="input"
                placeholder="https://whop.com/discover/..."
                value={formUrl}
                onChange={(e) => setFormUrl(e.target.value)}
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Keyword Target (pisahkan koma)</label>
              <input
                type="text"
                className="input"
                placeholder="ai tools, chatgpt, tutorial ai"
                value={formKeywords}
                onChange={(e) => setFormKeywords(e.target.value)}
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Hashtags Wajib</label>
              <input
                type="text"
                className="input"
                placeholder="#aitools, #nextgen"
                value={formHashtags}
                onChange={(e) => setFormHashtags(e.target.value)}
                style={{ fontSize: '0.813rem', padding: '6px 10px' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ flex: 1, padding: '8px', fontSize: '0.813rem' }}
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? 'Menyimpan...' : '💾 Simpan Campaign'}
              </button>
            </div>
          </form>
        )}

        {/* Target Goal Selector & Filter Control Bar */}
        <div
          style={{
            padding: '14px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
          }}
        >
          {/* Target Goal Calculator Header */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(59, 130, 246, 0.12) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🎯 Tentukan Target Cuan Per Video Anda:
                <span style={{ color: '#34d399', fontWeight: 800, fontSize: '1.05rem', backgroundColor: 'rgba(16,185,129,0.2)', padding: '2px 8px', borderRadius: '6px' }}>
                  ${targetGoalUSD} USD
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Sistem menghitung <b>berapa views yang kamu butuhkan</b> dan mengurutkan campaign yang <b>paling realistis dicapai pemula</b>.
              </div>
            </div>

            {/* Target Presets */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Target Cepat:</span>
              {[25, 50, 100, 200].map((val) => (
                <button
                  key={val}
                  onClick={() => setTargetGoalUSD(val)}
                  style={{
                    padding: '4px 12px',
                    borderRadius: '14px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    border: targetGoalUSD === val ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.12)',
                    backgroundColor: targetGoalUSD === val ? 'rgba(16, 185, 129, 0.25)' : 'rgba(255,255,255,0.04)',
                    color: targetGoalUSD === val ? '#34d399' : 'var(--text-secondary)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  ${val}
                </button>
              ))}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '4px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Custom: $</span>
                <input
                  type="number"
                  min="5"
                  max="5000"
                  value={targetGoalUSD}
                  onChange={(e) => setTargetGoalUSD(Math.max(1, Number(e.target.value)))}
                  style={{
                    width: '65px',
                    padding: '3px 8px',
                    fontSize: '0.75rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    backgroundColor: 'rgba(0,0,0,0.4)',
                    color: '#fff',
                  }}
                />
              </div>
            </div>
          </div>

          {/* Category Tabs & Sorting Options */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            {/* Category Filter Pills */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {CATEGORIES.map((cat) => {
                const isSelected = selectedCategory === cat.id;
                return (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      borderRadius: '16px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      border: isSelected ? '1px solid #3b82f6' : '1px solid var(--border-color)',
                      backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                      color: isSelected ? '#60a5fa' : 'var(--text-secondary)',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <span>{cat.icon}</span>
                    <span>{cat.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Whop Live Filter Toggle */}
            <button
              onClick={() => setOnlyWhopLive(!onlyWhopLive)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '14px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: onlyWhopLive ? '1px solid #22c55e' : '1px solid var(--border-color)',
                backgroundColor: onlyWhopLive ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                color: onlyWhopLive ? '#4ade80' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
              title="Tampilkan hanya campaign live yang ditarik dari Whop MCP"
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: onlyWhopLive ? '#22c55e' : '#64748b' }}></span>
              <span>Hanya Live MCP ({campaigns.filter((c) => c.isWhopLive || c.id.startsWith('bnty_')).length})</span>
            </button>

            {/* Search Input for Campaigns */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="text"
                placeholder="🔍 Cari nama / brand / keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  fontSize: '0.75rem',
                  padding: '5px 12px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'rgba(0,0,0,0.4)',
                  color: '#fff',
                  width: '220px',
                }}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    padding: '2px 6px',
                  }}
                  title="Reset pencarian"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Sorting Select */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Urutkan:</span>
              <select
                className="select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                style={{ fontSize: '0.75rem', padding: '4px 10px', backgroundColor: 'rgba(30,41,59,0.9)' }}
              >
                <option value="ease">🥇 Paling Mudah Capai Target (Rekomendasi)</option>
                <option value="views">📉 Kebutuhan Views Terendah</option>
                <option value="rate">💰 Rate Tertinggi ($/1K views)</option>
                <option value="budget">🛡️ Sisa Budget Terbanyak</option>
              </select>
            </div>
          </div>
        </div>

        {/* Campaign List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {isLoading ? (
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '40px' }}>
              Mengkalkulasi tingkat kemudahan target dan rating campaign...
            </p>
          ) : campaigns.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '60px' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>📂</div>
              <p>Belum ada campaign terdaftar untuk kategori ini.</p>
            </div>
          ) : (
            (() => {
              const filteredCampaigns = campaigns.filter((c) => {
                if (onlyWhopLive && !c.isWhopLive && !c.id.startsWith('bnty_')) {
                  return false;
                }
                if (!searchQuery.trim()) return true;
                const q = searchQuery.toLowerCase();
                return (
                  c.name.toLowerCase().includes(q) ||
                  c.creatorOrBrand.toLowerCase().includes(q) ||
                  c.targetKeywords.some((k) => k.toLowerCase().includes(q)) ||
                  c.notes.toLowerCase().includes(q)
                );
              });

              if (filteredCampaigns.length === 0) {
                return (
                  <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '60px' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🔍</div>
                    <p>Tidak ada campaign yang cocok dengan kriteria filter.</p>
                  </div>
                );
              }

              const sortedCampaigns = [...filteredCampaigns].sort((a, b) => {
                if (sortBy === 'ease') {
                  return b.rating.targetEaseScore - a.rating.targetEaseScore;
                }
                if (sortBy === 'views') {
                  const viewsA = Math.ceil((targetGoalUSD / Math.max(0.1, a.ratePerKViews)) * 1000);
                  const viewsB = Math.ceil((targetGoalUSD / Math.max(0.1, b.ratePerKViews)) * 1000);
                  return viewsA - viewsB;
                }
                if (sortBy === 'rate') {
                  return b.ratePerKViews - a.ratePerKViews;
                }
                if (sortBy === 'budget') {
                  return b.remainingBudget - a.remainingBudget;
                }
                return 0;
              });

              return sortedCampaigns.map((camp, idx) => {
                const viewsNeeded = Math.ceil((targetGoalUSD / Math.max(0.1, camp.ratePerKViews)) * 1000);
                const payoutSlots = Math.floor(camp.remainingBudget / Math.max(1, targetGoalUSD));
                const budgetPercent = Math.round((camp.remainingBudget / camp.totalBudget) * 100);

                // Ease level styling
                let easeBg = 'rgba(16, 185, 129, 0.15)';
                let easeColor = '#34d399';
                let easeBorder = 'rgba(16, 185, 129, 0.4)';
                let easeLabel = '🟢 SANGAT MUDAH DICAPAI';

                if (camp.rating.targetEaseLevel === 'easy') {
                  easeBg = 'rgba(59, 130, 246, 0.15)';
                  easeColor = '#60a5fa';
                  easeBorder = 'rgba(59, 130, 246, 0.4)';
                  easeLabel = '🟢 MUDAH DICAPAI';
                } else if (camp.rating.targetEaseLevel === 'moderate') {
                  easeBg = 'rgba(245, 158, 11, 0.15)';
                  easeColor = '#fbbf24';
                  easeBorder = 'rgba(245, 158, 11, 0.4)';
                  easeLabel = '🟡 SEDANG (PERLU HOOK KUAT)';
                } else if (camp.rating.targetEaseLevel === 'hard') {
                  easeBg = 'rgba(239, 68, 68, 0.15)';
                  easeColor = '#f87171';
                  easeBorder = 'rgba(239, 68, 68, 0.4)';
                  easeLabel = '🔴 BUTUH EFFORT TINGGI';
                }

                return (
                  <div
                    key={camp.id}
                    className="glass animate-fade-in"
                    style={{
                      borderRadius: 'var(--radius-md)',
                      padding: '18px 20px',
                      border: idx === 0 && sortBy === 'ease' ? '2px solid #10b981' : '1px solid var(--border-color)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '14px',
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      position: 'relative',
                    }}
                  >
                    {/* Top Recommended Tag for Rank 1 */}
                    {idx === 0 && sortBy === 'ease' && (
                      <div
                        style={{
                          position: 'absolute',
                          top: '-11px',
                          right: '20px',
                          backgroundColor: '#10b981',
                          color: '#0f172a',
                          fontWeight: 800,
                          fontSize: '0.688rem',
                          padding: '2px 10px',
                          borderRadius: '10px',
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        ⭐ Rekomendasi Paling Mudah #1
                      </div>
                    )}

                    {/* Top Bar: Title, Ease Badge & Category */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                      <div style={{ flex: 1, minWidth: '260px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                          {(camp.isWhopLive || camp.id.startsWith('bnty_')) && (
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontWeight: 800,
                                fontSize: '0.688rem',
                                backgroundColor: 'rgba(34, 197, 94, 0.2)',
                                color: '#4ade80',
                                border: '1px solid rgba(34, 197, 94, 0.4)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                            >
                              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#22c55e', display: 'inline-block' }}></span>
                              LIVE WHOP MCP
                            </span>
                          )}
                          {camp.spotsRemaining !== null && camp.spotsRemaining !== undefined && (
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontWeight: 700,
                                fontSize: '0.688rem',
                                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                                color: '#38bdf8',
                                border: '1px solid rgba(56, 189, 248, 0.3)',
                              }}
                            >
                              🎯 {camp.spotsRemaining} Spots Tersisa
                            </span>
                          )}
                          {camp.whopGoalType && (
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontWeight: 600,
                                fontSize: '0.688rem',
                                backgroundColor: 'rgba(148, 163, 184, 0.12)',
                                color: '#cbd5e1',
                                border: '1px solid rgba(148, 163, 184, 0.25)',
                              }}
                            >
                              📌 {camp.whopGoalType.replace('_', ' ')}
                            </span>
                          )}
                          <span
                            style={{
                              padding: '3px 10px',
                              borderRadius: '12px',
                              fontWeight: 800,
                              fontSize: '0.75rem',
                              backgroundColor: easeBg,
                              color: easeColor,
                              border: `1px solid ${easeBorder}`,
                            }}
                          >
                            {easeLabel} · Skor Kemudahan: {camp.rating.targetEaseScore}/100
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            Tier {camp.rating.tier} · Niche: <b>{camp.category}</b>
                          </span>
                        </div>
                        <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700 }}>
                          {camp.url ? (
                            <a
                              href={camp.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                color: 'var(--text-primary)',
                                textDecoration: 'none',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                transition: 'color 0.15s ease',
                              }}
                              onMouseEnter={(e) => (e.currentTarget.style.color = '#60a5fa')}
                              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                              title="Buka halaman resmi campaign di web (tab baru)"
                            >
                              {camp.name}
                              <span style={{ fontSize: '0.875rem', color: '#60a5fa' }}>↗</span>
                            </a>
                          ) : (
                            camp.name
                          )}
                        </h3>
                        <p style={{ margin: '2px 0 0', fontSize: '0.813rem', color: 'var(--text-secondary)' }}>
                          Oleh: <b>{camp.creatorOrBrand}</b>
                        </p>
                      </div>

                      {/* Reward Rate Badge */}
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Reward Rate</span>
                        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399' }}>
                          ${camp.ratePerKViews.toFixed(2)}{' '}
                          <span style={{ fontSize: '0.75rem', fontWeight: 400 }}>/ 1K views</span>
                        </div>
                      </div>
                    </div>

                    {/* HERO METRIC BANNER: How to reach user's target */}
                    <div
                      style={{
                        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '12px 16px',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '12px',
                      }}
                    >
                      {/* Metric 1: Views Needed */}
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Kebutuhan Views untuk ${targetGoalUSD}
                        </div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: viewsNeeded <= 15000 ? '#34d399' : viewsNeeded <= 35000 ? '#fbbf24' : '#f87171', marginTop: '2px' }}>
                          {viewsNeeded.toLocaleString('id-ID')}{' '}
                          <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>views</span>
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {viewsNeeded <= 15000 ? '⚡ Sangat realistis untuk pemula' : viewsNeeded <= 30000 ? '👍 Masih tergolong wajar' : '⚠️ Butuh video meledak'}
                        </div>
                      </div>

                      {/* Metric 2: Niche Virality */}
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Kemudahan FYP di Shorts
                        </div>
                        <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#60a5fa', marginTop: '4px' }}>
                          {camp.rating.nicheVirality.label}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {camp.rating.nicheVirality.audienceSize}
                        </div>
                      </div>

                      {/* Metric 3: Budget Capacity */}
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Keamanan Sisa Budget
                        </div>
                        <div style={{ fontSize: '1.05rem', fontWeight: 700, color: payoutSlots >= 30 ? '#34d399' : payoutSlots >= 10 ? '#fbbf24' : '#f87171', marginTop: '4px' }}>
                          {payoutSlots} Slot Tersisa
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          Sisa: ${camp.remainingBudget.toLocaleString()} dari ${camp.totalBudget.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* Explanation Box */}
                    <div
                      style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.03)',
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.813rem',
                        lineHeight: 1.4,
                      }}
                    >
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                        {camp.rating.easeExplanation}
                      </div>

                      {/* Budget Progress Bar */}
                      <div style={{ marginTop: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                          <span>Ketersediaan Anggaran Campaign:</span>
                          <span>{budgetPercent}% tersisa</span>
                        </div>
                        <div style={{ width: '100%', height: '5px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${budgetPercent}%`,
                              height: '100%',
                              backgroundColor: budgetPercent > 40 ? '#10b981' : budgetPercent > 20 ? '#f59e0b' : '#ef4444',
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Strategy Tips for reaching target */}
                    {camp.rating.strategyTips && camp.rating.strategyTips.length > 0 && (
                      <div
                        style={{
                          backgroundColor: 'rgba(59, 130, 246, 0.05)',
                          border: '1px dashed rgba(59, 130, 246, 0.25)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '10px 14px',
                        }}
                      >
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#93c5fd', marginBottom: '4px' }}>
                          💡 Tips Cepat Agar Klip Anda Tembus Target di Niche Ini:
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {camp.rating.strategyTips.map((tip, tIdx) => (
                            <li key={tIdx} style={{ marginBottom: '2px' }}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Target Keywords & Action */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Keyword Rekomendasi:</span>
                        {camp.targetKeywords.map((kw) => (
                          <button
                            key={kw}
                            className="btn"
                            style={{
                              fontSize: '0.75rem',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              backgroundColor: 'rgba(59, 130, 246, 0.1)',
                              border: '1px solid rgba(59, 130, 246, 0.3)',
                              color: '#93c5fd',
                              cursor: 'pointer',
                            }}
                            onClick={() => {
                              onSelectKeywordForResearch(kw);
                              onClose();
                            }}
                          >
                            🔍 {kw}
                          </button>
                        ))}
                      </div>

                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        {camp.url ? (
                          <a
                            href={camp.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary"
                            style={{
                              fontSize: '0.813rem',
                              padding: '6px 14px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              color: '#60a5fa',
                              borderColor: 'rgba(59, 130, 246, 0.5)',
                              backgroundColor: 'rgba(59, 130, 246, 0.12)',
                              textDecoration: 'none',
                              fontWeight: 600,
                            }}
                          >
                            🌐 Buka Web Campaign ↗
                          </a>
                        ) : (
                          <a
                            href={`https://whop.com/search/?query=${encodeURIComponent(camp.name)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary"
                            style={{
                              fontSize: '0.813rem',
                              padding: '6px 14px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              color: 'var(--text-secondary)',
                              borderColor: 'var(--border-color)',
                              backgroundColor: 'rgba(255, 255, 255, 0.03)',
                              textDecoration: 'none',
                            }}
                            title="Cari campaign ini di Whop"
                          >
                            🔍 Cari di Whop ↗
                          </a>
                        )}

                        <button
                          className="btn btn-primary"
                          style={{ fontSize: '0.813rem', padding: '6px 14px' }}
                          onClick={() => {
                            const primaryKw = camp.targetKeywords[0] || camp.name;
                            onSelectKeywordForResearch(primaryKw);
                            onClose();
                          }}
                        >
                          🚀 Riset Video Viral Niche Ini
                        </button>
                        <button
                          className="btn"
                          style={{
                            padding: '4px 8px',
                            fontSize: '0.75rem',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            color: '#f87171',
                            border: '1px solid rgba(239, 68, 68, 0.2)',
                          }}
                          onClick={() => {
                            if (confirm(`Hapus campaign "${camp.name}"?`)) {
                              deleteMutation.mutate(camp.id);
                            }
                          }}
                        >
                          Hapus
                        </button>
                      </div>
                    </div>
                  </div>
                );
              });
            })()
          )}
        </div>
      </div>
    </div>
  );
}
