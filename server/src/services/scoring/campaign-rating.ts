import type { Campaign, CampaignRating } from 'shared';

interface NicheBenchmark {
  demandScore: number;
  viralityScore: number;
  label: string;
  audienceSize: string;
  tips: string[];
}

const NICHE_BENCHMARKS: Record<string, NicheBenchmark> = {
  ai_tech: {
    demandScore: 88,
    viralityScore: 92,
    label: 'Viralitas Sangat Tinggi',
    audienceSize: 'Mass Appeal (Semua Kalangan)',
    tips: [
      'Gunakan format demonstrasi Before vs After dalam 2 detik pertama.',
      'Sebutkan nama tool AI gratis atau fitur unik yang memicu rasa penasaran.',
      'Tampilkan teks call-to-action link di bio/caption.',
    ],
  },
  gaming: {
    demandScore: 85,
    viralityScore: 95,
    label: 'Sangat Mudah FYP',
    audienceSize: 'Masif & Cepat Viral',
    tips: [
      'Pilih momen paling heboh (clutch, fail, funny moment) langsung di detik 0.',
      'Tambahkan sound effect atau zoom-in ekspresi streamer.',
      'Targetkan views cepat di 3 jam pertama setelah upload.',
    ],
  },
  entertainment: {
    demandScore: 85,
    viralityScore: 90,
    label: 'Viralitas Tinggi',
    audienceSize: 'Sangat Luas',
    tips: [
      'Buka dengan pertanyaan kontroversial atau hook emosional.',
      'Jaga ritme edit cepat dengan potongan setiap 1-2 detik.',
    ],
  },
  business_sidehustle: {
    demandScore: 84,
    viralityScore: 82,
    label: 'Tinggi untuk Pencari Cuan',
    audienceSize: 'Pencari Passive Income',
    tips: [
      'Tampilkan angka/hasil konkret di detik awal (misal: "Hasilkan $50/hari dari rumah").',
      'Hindari penjelasan berbelit; langsung ke tutorial langkah 1.',
    ],
  },
  finance_crypto: {
    demandScore: 90,
    viralityScore: 72,
    label: 'Rate Tinggi, Niche Tertarget',
    audienceSize: 'Niche Spesifik',
    tips: [
      'Gunakan istilah sederhana yang dipahami pemula (hindari jargon berat).',
      'Sorot momentum market atau berita trending crypto terbaru.',
      'Rate per views sangat besar, jadi tidak butuh jutaan views untuk hasil besar.',
    ],
  },
  fitness_lifestyle: {
    demandScore: 78,
    viralityScore: 80,
    label: 'Menengah ke Tinggi',
    audienceSize: 'Gaya Hidup & Kesehatan',
    tips: [
      'Fokus pada tips cepat (misal: kesalahan umum saat workout).',
      'Visual sebelum & sesudah sangat efektif menarik retensi.',
    ],
  },
  other: {
    demandScore: 70,
    viralityScore: 70,
    label: 'Standar',
    audienceSize: 'Bervariasi',
    tips: [
      'Uji coba beberapa variasi hook di 3 detik pertama.',
      'Pastikan caption dan hashtag sesuai ketentuan campaign.',
    ],
  },
};

/**
 * Pure function to calculate Campaign Opportunity & Target Feasibility Rating
 */
export function calculateCampaignRating(campaign: Campaign): CampaignRating {
  const rate = Math.max(0.1, campaign.ratePerKViews);
  const niche = NICHE_BENCHMARKS[campaign.category] ?? NICHE_BENCHMARKS['other']!;

  // 1. Earning Score (0 - 100) — based on rate per 1K views (RPM)
  // $1/1K is ~25, $3.5/1K is ~70, $5+/1K is 90-100
  const earningScore = Math.min(100, Math.round((rate / 5.5) * 100));

  // 2. Budget Health Score & Safety
  let budgetScore = 50;
  let budgetHealth: 'safe' | 'moderate' | 'low' = 'moderate';
  let budgetRunwayScore = 60;

  if (campaign.remainingBudget >= 2500) {
    budgetScore = 100;
    budgetHealth = 'safe';
    budgetRunwayScore = 100;
  } else if (campaign.remainingBudget >= 1200) {
    budgetScore = 80;
    budgetHealth = 'safe';
    budgetRunwayScore = 85;
  } else if (campaign.remainingBudget >= 500) {
    budgetScore = 60;
    budgetHealth = 'moderate';
    budgetRunwayScore = 60;
  } else {
    budgetScore = 30;
    budgetHealth = 'low';
    budgetRunwayScore = 25;
  }

  // 3. Demand Score
  const demandScore = niche.demandScore;

  // 4. Calculate Views Needed for Target Earnings ($25, $50, $100)
  const viewsFor25 = Math.ceil((25 / rate) * 1000);
  const viewsFor50 = Math.ceil((50 / rate) * 1000);
  const viewsFor100 = Math.ceil((100 / rate) * 1000);

  // 5. Target Feasibility / Ease Score (0 - 100)
  // Evaluates how realistic it is for a creator to reach the $50 target
  // a) Views burden score: Fewer views needed = Much easier!
  let viewsBurdenScore = 50;
  if (viewsFor50 <= 10000) {
    viewsBurdenScore = 100;
  } else if (viewsFor50 <= 15000) {
    viewsBurdenScore = 85;
  } else if (viewsFor50 <= 25000) {
    viewsBurdenScore = 70;
  } else if (viewsFor50 <= 40000) {
    viewsBurdenScore = 50;
  } else {
    viewsBurdenScore = 25;
  }

  // b) Weighted Target Ease Score
  // 40% Views Requirement + 35% Niche Virality / FYP Ease + 25% Budget Runway
  const rawEaseScore =
    viewsBurdenScore * 0.40 +
    niche.viralityScore * 0.35 +
    budgetRunwayScore * 0.25;

  const targetEaseScore = Math.min(100, Math.max(0, Math.round(rawEaseScore)));

  // c) Target Ease Level Classification
  let targetEaseLevel: 'very_easy' | 'easy' | 'moderate' | 'hard' = 'moderate';
  if (targetEaseScore >= 80) {
    targetEaseLevel = 'very_easy';
  } else if (targetEaseScore >= 65) {
    targetEaseLevel = 'easy';
  } else if (targetEaseScore >= 50) {
    targetEaseLevel = 'moderate';
  } else {
    targetEaseLevel = 'hard';
  }

  // d) Budget Safety Pockets (Number of $50 target claims remaining before budget exhausts)
  const budgetSafetyPockets = Math.max(0, Math.floor(campaign.remainingBudget / 50));

  // e) Human Explanation for Ease
  let easeExplanation = '';
  if (targetEaseLevel === 'very_easy') {
    easeExplanation = `🎯 Sangat Mudah: Cukup butuh ${viewsFor50.toLocaleString('id-ID')} views untuk target $50 di niche ${niche.label} dengan sisa budget sangat aman (${budgetSafetyPockets} slot payout tersisa).`;
  } else if (targetEaseLevel === 'easy') {
    easeExplanation = `🚀 Mudah Dicapai: Butuh ${viewsFor50.toLocaleString('id-ID')} views untuk $50. Niche ${campaign.category} memiliki audience luas dan budget masih mencukupi.`;
  } else if (targetEaseLevel === 'moderate') {
    easeExplanation = `⚖️ Sedang: Membutuhkan ${viewsFor50.toLocaleString('id-ID')} views. Perlu hook kuat di 3 detik pertama agar klip menembus algoritma.`;
  } else {
    easeExplanation = `⚠️ Butuh Effort Ekstra: Memerlukan ${viewsFor50.toLocaleString('id-ID')} views atau sisa budget menipis ($${campaign.remainingBudget}), berisiko kehabisan budget sebelum target tercapai.`;
  }

  // 6. Weighted Total Opportunity Score (0 - 100)
  // Combines Earning + Budget + Demand + Target Feasibility
  const rawScore =
    earningScore * 0.25 +
    budgetScore * 0.20 +
    demandScore * 0.20 +
    targetEaseScore * 0.35;

  const opportunityScore = Math.round(rawScore);

  // 7. Determine Tier
  let tier: 'S' | 'A' | 'B' | 'C' = 'B';
  let verdict = '';

  if (opportunityScore >= 80) {
    tier = 'S';
    verdict = '🔥 Rekomendasi Utama: Sangat mudah tembus target dan potensi pendapatan tinggi!';
  } else if (opportunityScore >= 65) {
    tier = 'A';
    verdict = '🚀 Sangat Potensial: Peluang target tercapai tinggi dengan estimasi payout menguntungkan.';
  } else if (opportunityScore >= 50) {
    tier = 'B';
    verdict = '⚖️ Potensi Menengah: Target bisa dicapai dengan optimasi hook klip yang menarik.';
  } else {
    tier = 'C';
    verdict = '⚠️ Kurang Direkomendasikan: Target lebih sulit dicapai atau sisa budget menipis.';
  }

  // 8. Projected Earnings Simulation
  const projectedEarnings = {
    views10k: Math.round(10 * rate),
    views50k: Math.round(50 * rate),
    views100k: Math.round(100 * rate),
    views500k: Math.round(500 * rate),
  };

  return {
    campaignId: campaign.id,
    tier,
    opportunityScore,
    earningScore,
    demandScore,
    budgetScore,
    projectedEarnings,
    budgetHealth,
    verdict,
    targetEaseLevel,
    targetEaseScore,
    viewsNeededForTarget: {
      for25USD: viewsFor25,
      for50USD: viewsFor50,
      for100USD: viewsFor100,
    },
    nicheVirality: {
      score: niche.viralityScore,
      label: niche.label,
      audienceSize: niche.audienceSize,
    },
    budgetSafetyPockets,
    easeExplanation,
    strategyTips: niche.tips,
  };
}
