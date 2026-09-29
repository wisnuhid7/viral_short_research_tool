# AGENTS.md

Aturan untuk AI coding agent (dan kontributor) di proyek **Viral Shorts Research & Clip Planner**. Baca file ini sebelum mengubah kode. Rujukan produk lengkap ada di `PRD_Viral_Shorts_Research_Tool.md`.

## 1. Tentang Proyek

Tool **pribadi (single-user)** untuk riset YouTube Shorts viral berdasarkan keyword: skor viralitas, ringkasan hook dan struktur, saran keyword, saran judul/caption, dan pencocokan dengan campaign Whop Content Rewards.

## 2. Aturan Keras (tidak boleh dilanggar)

1. **Dilarang membuat fitur mengunduh, menyalin, atau mengekstrak file video/audio** dari YouTube atau platform lain. Tidak ada `yt-dlp`, scraper stream, atau sejenisnya.
2. **Dilarang membuat fitur auto-posting massal** atau otomatisasi akun sosial tanpa persetujuan eksplisit pemilik proyek.
3. **Rahasia tidak boleh ada di frontend.** API key YouTube, Whop, dan LLM hanya dibaca di `server/` lewat environment variable. Jangan gunakan prefix `VITE_` untuk rahasia apa pun.
4. **Jangan commit rahasia.** `.env` harus ada di `.gitignore`; sediakan `.env.example` tanpa nilai asli.
5. **Whop bersifat read-only secara default.** Jangan memanggil tool/endpoint yang memindahkan uang atau mengubah data (payout, transfer, refund, trades, cashback, dsb.). Aksi tulis hanya boleh atas permintaan eksplisit pemilik proyek dan harus melewati langkah konfirmasi.
6. **Jangan mengarang data.** Jika data YouTube/Whop tidak tersedia, tampilkan status kosong atau "tidak tersedia", bukan angka tebakan.
7. **Judul dan caption yang dihasilkan tidak boleh menyesatkan** (tidak sesuai isi) dan harus dicek terhadap aturan caption campaign. Selalu disetujui manual oleh pengguna sebelum dipakai.

## 3. Stack

| Lapisan | Pilihan |
|---|---|
| Frontend | Vite + React + TypeScript, TanStack Query, Tailwind |
| Backend | Node.js (TypeScript), Fastify atau Express |
| Database | SQLite via `better-sqlite3` |
| Antrean/job | `p-queue` di proses Node; `node-cron` untuk fase 3 |
| Repo | Monorepo: `web/`, `server/`, `shared/` |

Jangan menambah dependency besar (ORM berat, state manager global, UI kit tambahan) tanpa alasan tertulis. Prioritaskan sederhana dan mudah dirawat.

## 4. Struktur Repo

```
/
├── AGENTS.md
├── PRD_Viral_Shorts_Research_Tool.md
├── web/               # Vite + React (SPA)
│   └── src/
├── server/            # Node.js API
│   └── src/
│       ├── routes/        # endpoint HTTP tipis
│       ├── services/      # youtube, whop, llm, scoring, summarizer
│       ├── db/            # skema, migrasi, query
│       └── lib/           # util, config, logger
├── shared/            # tipe TypeScript dan skema validasi bersama
└── .env.example
```

- Route hanya validasi input dan memanggil service. Logika bisnis ada di `services/`.
- Frontend hanya memanggil API backend (`/api/*`), tidak pernah memanggil YouTube/Whop/LLM langsung.
- Tipe dan skema (mis. Zod) yang dipakai kedua sisi ditaruh di `shared/`.

## 5. Perintah Umum

Sesuaikan jika script berubah, dan perbarui bagian ini saat menambah script baru.

```bash
npm install            # dari root (workspaces)
npm run dev            # jalankan web + server bersamaan
npm run dev:web        # hanya frontend
npm run dev:server     # hanya backend
npm run build          # build semua
npm run typecheck      # tsc --noEmit di semua paket
npm run lint
npm test
```

Jalankan `typecheck`, `lint`, dan `test` sebelum menyatakan pekerjaan selesai.

## 6. Konvensi Kode

- TypeScript `strict: true`. Hindari `any`; gunakan `unknown` lalu validasi.
- Validasi semua input eksternal (request, respons API pihak ketiga, output LLM) dengan skema (Zod).
- Nama file: `kebab-case`; komponen React: `PascalCase`; fungsi/variabel: `camelCase`; konstanta: `UPPER_SNAKE_CASE`.
- Fungsi kecil dan satu tanggung jawab. Hindari file lebih dari sekitar 300 baris.
- Penanganan error eksplisit: jangan menelan error diam-diam. Kembalikan error terstruktur `{ code, message }` dari API.
- Log lewat logger terpusat; **jangan log API key, token, atau respons mentah yang sensitif**.
- Komentar menjelaskan *mengapa*, bukan *apa*.
- Teks UI dan pesan kepada pengguna dalam Bahasa Indonesia; kode, nama variabel, dan komentar teknis dalam Bahasa Inggris.

## 7. Aturan Integrasi

### YouTube Data API
- Kuota default 10.000 unit/hari. `search.list` = 100 unit; `videos.list` dan `channels.list` = 1 unit. Karena itu: satu pencarian, lalu ambil statistik dengan `videos.list` secara batch (sampai 50 ID per panggilan).
- **Wajib cache** hasil pencarian dan statistik (default 24 jam). Cek cache sebelum memanggil API.
- Sediakan penghitung kuota harian dan hentikan panggilan dengan pesan jelas saat mendekati batas.
- Tangani `quotaExceeded` dengan baik (jangan retry tanpa henti).
- Deteksi Shorts memakai heuristik (durasi maksimum 3 menit, `#shorts`); tidak ada flag resmi, jadi tandai hasilnya sebagai perkiraan.
- Patuhi ToS YouTube API (atribusi, batas penyimpanan data).

### LLM (Claude API)
- Panggil hanya untuk video/segmen yang dipilih pengguna, bukan seluruh hasil pencarian.
- Minta output **JSON terstruktur**, validasi dengan skema, dan tangani JSON rusak (retry terbatas).
- Cache ringkasan permanen per `video_id` + versi prompt.
- Simpan prompt di satu tempat (`server/src/services/prompts/`) dengan versi.
- Jika transkrip tidak ada, gunakan fallback judul + deskripsi dan tandai `confidence: "low"`.

### Whop (API/MCP)
- Read-only secara default (lihat aturan keras 5).
- Gunakan kredensial read-only untuk aplikasi; jangan menyematkan kredensial admin penuh.
- Validasi dulu data apa yang benar-benar tersedia (bounty, ledger) sebelum membangun fitur di atasnya. Jika daftar campaign publik tidak tersedia, sediakan input campaign manual.
- Data campaign (rate, budget, aturan) bisa berubah; tampilkan waktu terakhir diperbarui.

## 8. Skor & Rekomendasi

- Rumus skor viral dan skor keyword ada di PRD (bagian 7 dan 7A). Implementasikan di `server/src/services/scoring/` sebagai fungsi murni agar mudah diuji.
- Bobot berada di konfigurasi, bukan hardcode tersebar.
- Selalu tampilkan komponen skor (velocity, reach, engagement, dsb.) dan jumlah sampel agar pengguna bisa menilai keandalannya.
- Video berumur di bawah 3 jam diberi penalti kepercayaan.

## 9. Database

- Migrasi berversi; jangan mengubah skema tanpa file migrasi.
- Tabel inti: `videos`, `channels`, `keyword_searches`, `keyword_suggestions`, `summaries`, `collections`, `campaigns`, `title_options`, `clip_logs`.
- Simpan hanya metadata publik dan catatan pengguna. Jangan menyimpan file media.
- Gunakan transaksi untuk operasi multi-tabel.

## 10. Testing

- Uji unit wajib untuk fungsi skor, normalisasi, parsing respons API, dan validasi skema.
- Mock semua panggilan eksternal (YouTube, Whop, LLM); tes tidak boleh memakai kuota atau kredensial asli.
- Sediakan fixture respons contoh di `server/test/fixtures/`.
- Bug diperbaiki dengan tes yang mereproduksinya terlebih dahulu bila memungkinkan.

## 11. UI/UX

- Halaman utama: pencarian keyword → daftar hasil bersorting skor → panel detail (ringkasan, pola hook).
- Tampilkan state loading, kosong, dan error di setiap daftar dan panel.
- Tampilkan sisa kuota YouTube hari ini dan waktu terakhir data di-cache.
- Peringatan tetap terlihat: "Gunakan hanya sebagai referensi. Klip untuk Whop harus dari footage resmi campaign."
- Aksesibilitas dasar: label pada input, kontras memadai, navigasi keyboard.

## 12. Alur Kerja Agent

1. Baca `PRD_Viral_Shorts_Research_Tool.md` dan file ini sebelum memulai tugas besar.
2. Kerjakan perubahan kecil dan terfokus; jelaskan rencana singkat untuk perubahan yang menyentuh banyak file.
3. Jangan mengubah cakupan produk secara diam-diam. Jika tugas bertentangan dengan PRD atau aturan keras, berhenti dan tanyakan.
4. Jika ada keputusan yang belum ditentukan (lihat "Pertanyaan Terbuka" di PRD), tanyakan kepada pemilik proyek, jangan menebak.
5. Sebelum selesai: jalankan `typecheck`, `lint`, dan `test`, lalu ringkas apa yang diubah, bagaimana diuji, dan apa yang belum selesai.
6. Commit kecil dengan pesan jelas (format Conventional Commits, mis. `feat(server): add viral score service`).

## 13. Definition of Done

- [ ] Sesuai PRD dan tidak melanggar aturan keras.
- [ ] Tidak ada rahasia di kode, log, atau frontend.
- [ ] Input eksternal divalidasi; error ditangani.
- [ ] Panggilan API eksternal memakai cache dan menghormati kuota.
- [ ] Tes relevan ditambahkan dan lulus; `typecheck` dan `lint` bersih.
- [ ] README/PRD/AGENTS.md diperbarui bila perilaku atau perintah berubah.

## 14. Di Luar Cakupan (jangan dikerjakan tanpa persetujuan)

- Multi-user, login, billing, atau fitur SaaS.
- Pengunduhan video, penyalinan konten, atau auto-posting massal.
- Editor video (integrasi tool lain dibahas terpisah).
- Aksi finansial di Whop (payout, transfer, refund, trading).
