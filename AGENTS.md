# AGENTS.md

Panduan untuk AI coding agent di proyek **Viral Shorts Research & Clip Planner**. Rujukan produk ada di `PRD_Viral_Shorts_Research_Tool.md`. File ini berisi panduan kerja, bukan daftar larangan: agent bebas mengambil keputusan teknis dan mengerjakan tugas apa pun dari pemilik proyek.

## 1. Tentang Proyek

Tool **pribadi (single-user)** untuk riset YouTube Shorts berdasarkan keyword: skor viralitas, ringkasan hook dan struktur, saran keyword, saran judul/caption, dan pencocokan dengan campaign Whop Content Rewards. Cakupan boleh berkembang sesuai kebutuhan pemilik proyek.

## 2. Prinsip Kerja

1. Ikuti permintaan pemilik proyek. Tidak perlu meminta izin untuk perubahan cakupan, refactor, atau penambahan dependency; cukup jelaskan singkat apa yang dilakukan dan alasannya.
2. Ambil keputusan sendiri untuk hal yang belum ditentukan, catat asumsinya di ringkasan akhir.
3. Boleh mengerjakan fitur di luar PRD, termasuk multi-user, editor video, otomatisasi posting, dan integrasi tulis ke Whop, selama diminta pemilik proyek.
4. Jaga kebersihan dasar: simpan rahasia (API key YouTube, Whop, LLM) di environment variable pada `server/`, jangan commit `.env`, dan sediakan `.env.example`.
5. **Fitur unduh video YouTube diperbolehkan** (lihat bagian 7A) untuk video yang boleh dipakai pemilik proyek. Agent boleh membangun dan menjalankan fiturnya, termasuk memakai `yt-dlp`.

## 3. Stack

| Lapisan | Pilihan awal (boleh diganti) |
|---|---|
| Frontend | Vite + React + TypeScript, TanStack Query, Tailwind |
| Backend | Node.js (TypeScript), Fastify atau Express |
| Database | SQLite via `better-sqlite3` |
| Antrean/job | `p-queue`, `node-cron` |
| Repo | Monorepo: `web/`, `server/`, `shared/` |

Dependency baru boleh ditambahkan bila membantu.

## 4. Struktur Repo

```
/
├── AGENTS.md
├── PRD_Viral_Shorts_Research_Tool.md
├── web/               # Vite + React (SPA)
├── server/
│   └── src/
│       ├── routes/        # endpoint HTTP tipis
│       ├── services/      # youtube, whop, llm, scoring, summarizer
│       ├── db/            # skema, migrasi, query
│       └── lib/           # util, config, logger
├── shared/            # tipe dan skema bersama
└── .env.example
```

Struktur ini saran; ubah bila ada susunan yang lebih baik.

## 5. Perintah Umum

```bash
npm install
npm run dev
npm run dev:web
npm run dev:server
npm run build
npm run typecheck
npm run lint
npm test
```

Perbarui daftar ini saat script berubah.

## 6. Konvensi Kode

- TypeScript `strict: true`; validasi input eksternal dengan Zod bila praktis.
- Nama file `kebab-case`, komponen `PascalCase`, fungsi/variabel `camelCase`, konstanta `UPPER_SNAKE_CASE`.
- Fungsi kecil dan fokus; tangani error secara eksplisit dan kembalikan `{ code, message }` dari API.
- Komentar menjelaskan *mengapa*, bukan *apa*.
- Teks UI dalam Bahasa Indonesia; kode dan komentar teknis dalam Bahasa Inggris.

## 7. Catatan Integrasi

### YouTube Data API
- Kuota default 10.000 unit/hari; `search.list` = 100 unit, `videos.list`/`channels.list` = 1 unit. Gunakan `videos.list` secara batch (sampai 50 ID).
- Cache hasil (default 24 jam) dan tampilkan sisa kuota agar mudah dipantau.
- Deteksi Shorts memakai heuristik (durasi, `#shorts`), tandai sebagai perkiraan.

### LLM (Claude API)
- Minta output JSON terstruktur, validasi, dan retry bila rusak.
- Cache ringkasan per `video_id` + versi prompt; simpan prompt di `server/src/services/prompts/`.
- Tanpa transkrip, gunakan judul + deskripsi dan tandai `confidence: "low"`.

### Whop (API/MCP)
- Akses baca maupun tulis diizinkan sesuai kebutuhan dan permintaan pemilik proyek.
- Data campaign bisa berubah; tampilkan waktu terakhir diperbarui. Bila daftar campaign publik tidak tersedia, sediakan input manual.

### 7A. Fitur Unduh Video (diperbolehkan)

Agent boleh membuat tool untuk mengunduh video YouTube (mis. lewat `yt-dlp`), menyimpannya secara lokal, dan mengaitkannya dengan record `videos` atau `campaigns`. Panduan implementasi:

- **Sumber yang sah:** footage resmi campaign Whop, video di channel milik pengguna, konten Creative Commons, atau video dengan izin tertulis pemilik. Simpan kolom `source_rights` (mis. `campaign_official`, `own`, `cc`, `permission`) dan `source_note` agar jelas dasar pemakaiannya.
- **Pengecekan sebelum unduh:** UI meminta pengguna memilih dasar hak pakai. Jangan unduh bila tidak ada pilihan yang dipilih.
- **Jalankan hanya di `server/`** (`services/downloader/`), tidak pernah dari frontend. Gunakan antrean `p-queue` dengan batas konkurensi kecil dan timeout.
- **Penyimpanan:** folder lokal terpisah (mis. `server/storage/media/`), masuk `.gitignore`. Sediakan batas ukuran total dan tombol hapus.
- **Validasi input:** hanya terima URL YouTube yang valid (Zod), jangan teruskan string mentah ke shell; gunakan argumen array, bukan interpolasi string.
- **Jangan menyematkan hasil unduhan ke auto-posting massal** kecuali diminta pemilik proyek.
- Catat unduhan di `clip_logs` (waktu, URL, dasar hak pakai).
- Tampilkan peringatan: "Unduh hanya video yang Anda berhak pakai. Footage untuk Whop harus dari sumber resmi campaign."

## 8. Skor & Rekomendasi

- Rumus skor ada di PRD (bagian 7 dan 7A); implementasikan sebagai fungsi murni di `server/src/services/scoring/` dengan bobot di konfigurasi.
- Tampilkan komponen skor dan jumlah sampel agar hasil mudah dinilai.

## 9. Database

- Gunakan migrasi berversi. Tabel inti: `videos`, `channels`, `keyword_searches`, `keyword_suggestions`, `summaries`, `collections`, `campaigns`, `title_options`, `clip_logs`, `media_files`. Tabel lain boleh ditambah.
- Gunakan transaksi untuk operasi multi-tabel.

## 10. Testing

- Tulis tes untuk logika penting (skor, normalisasi, parsing, validasi). Mock panggilan eksternal bila memungkinkan; fixture di `server/test/fixtures/`.

## 11. UI/UX

- Alur utama: pencarian keyword → daftar hasil bersorting skor → panel detail.
- Sediakan state loading, kosong, dan error; tampilkan sisa kuota dan waktu cache.
- Perhatikan aksesibilitas dasar.

## 12. Alur Kerja Agent

1. Baca PRD dan file ini sebelum tugas besar.
2. Kerjakan langsung; jelaskan rencana hanya bila perubahan luas.
3. Sebelum selesai, jalankan `typecheck`, `lint`, dan `test` bila tersedia.
4. Ringkas apa yang diubah, cara pengujian, asumsi, dan sisa pekerjaan.
5. Commit dengan Conventional Commits, mis. `feat(server): add viral score service`.