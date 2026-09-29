# Viral Shorts Research & Clip Planner

Tool pribadi (single-user) untuk riset YouTube Shorts viral berbasis keyword: perhitungan skor viralitas, ekstraksi pola hook dan struktur video, saran keyword turunan, pencatatan koleksi referensi, dan ekspor data riset (CSV & Markdown).

> ⚠️ **Peringatan & Etika Penggunaan:**  
> Tool ini **hanya sebagai referensi riset ide dan struktur konten**, BUKAN untuk menyalin, mengunduh, atau me-repost video orang lain. Klip untuk campaign Whop Rewards wajib dibuat dari footage resmi campaign.

---

## 🚀 Fitur Utama

1. **Pencarian YouTube Shorts Berbasis Keyword & Filter**
   - Filter rentang waktu: 24 Jam Terakhir, 7 Hari Terakhir, 30 Hari Terakhir.
   - Filter durasi maksimal (30s, 60s, 90s, 180s) dan bahasa.
   - Deteksi format Shorts otomatis.

2. **Perhitungan Skor Viralitas Multi-Faktor**
   - **Velocity (45%)**: Laju pertambahan views per jam sejak diunggah.
   - **Reach Ratio (30%)**: Rasio views terhadap subscriber channel (kemampuan menembus algoritma di luar penonton langganan).
   - **Engagement Rate (25%)**: Rasio interaksi (likes + comments) terhadap total views.
   - **Confidence Penalty**: Penalti keandalan untuk video berusia < 3 jam.

3. **Analisis Struktur & Hook Video (LLM OpenAI GPT-4o-mini)**
   - Ekstraksi 3 detik pertama (hook verbal/visual).
   - Pola hook & breakdown struktur 3 bagian: *Hook*, *Body*, *Call-to-Action (CTA)*.
   - Gaya presentasi & momen-momen kunci (*Key Moments*).
   - Cache otomatis hasil ringkasan per video & versi prompt.

4. **Saran Keyword Turunan (*Keyword Suggestions*)**
   - Menggali tag video populer dan kata kunci judul yang sering muncul secara otomatis dari hasil pencarian.
   - Pencarian cepat satu klik untuk eksplorasi niche lebih dalam.

5. **Koleksi & Ekspor Riset**
   - Simpan video referensi ke dalam koleksi custom beserta catatan.
   - Ekspor hasil riset ke format **CSV** dan **Markdown** (lengkap dengan ringkasan struktur bila ada).

6. **Quota Tracker & Proteksi API**
   - Indikator penggunaan kuota harian YouTube API secara real-time.
   - Cache SQLite 24 jam untuk meminimalisir konsumsi kuota.

---

## 🛠️ Arsitektur & Teknologi

- **Frontend (`web/`)**: Vite + React + TypeScript, TanStack Query, Tailwind CSS, Lucide Icons.
- **Backend (`server/`)**: Node.js + Express (TypeScript), `@anthropic-ai/sdk`, `p-queue`.
- **Database**: SQLite lokal via `better-sqlite3` dengan migrasi skema otomatis.
- **Shared (`shared/`)**: Tipe TypeScript dan skema validasi `zod` bersama.

---

## 📦 Panduan Menjalankan

### 1. Prasyarat
- Node.js >= 20.0.0
- YouTube Data API v3 Key (Google Cloud Console)
- OpenAI API Key

### 2. Konfigurasi Environment
Salin `.env.example` menjadi `.env` di root repository dan isi API key:

```bash
cp .env.example .env
```

Isi variabel:
```env
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PORT=3001
NODE_ENV=development
YOUTUBE_DAILY_QUOTA_LIMIT=10000
CACHE_TTL_HOURS=24
```

### 3. Instalasi Dependency
```bash
npm install
```

### 4. Menjalankan Aplikasi (Development)
Menjalankan backend API (`http://localhost:3001`) dan frontend (`http://localhost:5173`) secara bersamaan:

```bash
npm run dev
```

Atau jalankan secara terpisah:
- Backend: `npm run dev:server`
- Frontend: `npm run dev:web`

### 5. Build, Typecheck, & Testing
- **Build Semua**: `npm run build`
- **Typecheck**: `npm run typecheck`
- **Jalankan Unit Test**: `npm test`

---

## 🔒 Keamanan & Kebijakan

1. **Zero Client Secret**: Semua API Key hanya tersimpan di server (`.env`) dan tidak pernah dikirim ke frontend.
2. **Read-Only Data Whop & YouTube**: Tidak ada aksi transaksi finansial atau manipulasi data publik.
3. **No Video Downloader / Scraper**: Mematuhi ketentuan YouTube Data API v3 Terms of Service.
