# PRD: Viral Shorts Research & Clip Planner

**Versi:** 0.4 (Draft, stack: Vite + Node.js) · **Tanggal:** 29 September 2026 · **Owner:** Wisnu Hidayatullah

---

## 1. Ringkasan

Tool untuk mencari YouTube Shorts yang sedang viral berdasarkan keyword, menghitung skor viralitas, meringkas isinya (hook, struktur, topik), lalu menghubungkannya dengan campaign Whop Content Rewards yang relevan. Output tool ini adalah **referensi format dan strategi editing**, bukan bahan untuk di-repost.

**Prinsip utama:** klip yang diposting ke Whop hanya boleh berasal dari footage resmi yang disediakan campaign. Shorts viral milik pihak lain dipakai sebagai *riset pola* (hook, durasi, gaya subtitle), bukan sebagai sumber klip.

## 2. Latar Belakang & Masalah

| Masalah | Dampak |
|---|---|
| Memilih niche/campaign Whop dilakukan dengan menebak | Waktu terbuang pada campaign yang budget-nya cepat habis atau niche-nya sepi |
| Tidak ada cara cepat mengetahui hook dan format apa yang sedang bekerja | Klip kurang kompetitif, view rendah, penghasilan kecil |
| Menonton banyak Shorts manual untuk riset sangat lambat | Kecepatan posting rendah padahal budget campaign bersifat first-come-first-served |
| Rate Whop bervariasi (sekitar $0,20–$6 per 1.000 view) | Perlu prioritas campaign berdasarkan potensi, bukan sekadar rate tertinggi |

## 3. Tujuan & Non-Tujuan

### Tujuan
1. Menemukan Shorts viral per keyword dalam kurang dari 30 detik.
2. Menghasilkan ringkasan hook + pola struktur per video secara otomatis.
3. Merekomendasikan campaign Whop yang paling cocok dengan tren keyword.
4. Melacak hasil (view, earning) untuk mengukur ROI tiap niche.
5. Membantu memilih keyword yang ramai peminat tetapi belum jenuh.
6. Membantu memilih judul dan caption klip berdasarkan pola yang terbukti, lalu belajar dari hasil klip sendiri.

### Non-Tujuan (di luar cakupan)
- Mengunduh atau menyalin video pihak lain untuk diposting ulang.
- Auto-posting massal ke banyak akun (risiko spam/ban, dievaluasi terpisah).
- Mengedit video (bisa integrasi tool lain seperti OpusClip di fase lanjut).
- Menjamin penghasilan.

## 4. Pengguna Target

**Persona utama: Clipper solo (Wisnu).** Mengerjakan 2–5 campaign Whop, ingin riset cepat, bekerja dengan waktu terbatas, level teknis menengah.

**Keputusan:** tool dipakai pribadi (single-user). Tidak ada multi-user, login, atau billing. Jika suatu hari dibuka untuk orang lain, itu proyek terpisah dengan PRD baru.

## 5. User Stories

| # | Sebagai clipper, saya ingin... | Agar... | Prioritas |
|---|---|---|---|
| U1 | mencari Shorts viral dengan keyword dan rentang waktu tertentu | tahu apa yang sedang tren | P0 |
| U2 | melihat skor viralitas tiap video | cepat menyaring yang benar-benar performa tinggi | P0 |
| U3 | membaca ringkasan hook dan alur video | mempelajari polanya tanpa menonton semua | P0 |
| U4 | menyimpan video/keyword ke koleksi referensi | membangun perpustakaan inspirasi | P0 |
| U5 | melihat daftar campaign Whop beserta rate, sisa budget, dan aturan | memilih campaign yang layak | P1 |
| U6 | melihat rekomendasi campaign berdasarkan keyword tren | menghubungkan riset dengan uang | P1 |
| U7 | mencatat klip yang saya posting dan hasilnya | tahu niche mana yang menguntungkan | P1 |
| U8 | menerima notifikasi saat keyword tertentu melonjak | bergerak cepat sebelum jenuh | P2 |
| U9 | menganalisis transkrip footage campaign untuk menemukan momen terbaik | mempercepat proses memilih segmen klip | P2 |
| U10 | mendapat saran keyword turunan dari satu keyword awal | menemukan sudut yang belum terpikirkan | P0 |
| U11 | melihat skor keyword (peminat vs kompetisi) | memilih keyword yang peluangnya terbaik | P1 |
| U12 | mendapat 5-10 opsi judul dan caption untuk klip saya, lalu memilih dan mengedit | menghemat waktu dan memakai pola yang terbukti | P1 |
| U13 | melihat riwayat judul yang saya pakai beserta view-nya | tahu pola judul mana yang berhasil untuk saya | P1 |
| U14 | diingatkan syarat caption campaign (hashtag, mention, kata wajib) | klip tidak ditolak karena aturan | P1 |

## 6. Fitur & Ruang Lingkup

### MVP (P0) – target 2–3 minggu
1. **Pencarian keyword.** Input keyword, filter: rentang upload (24 jam / 7 hari / 30 hari), bahasa, durasi maksimum.
2. **Daftar hasil.** Thumbnail, judul, channel, view, like, komentar, umur video, skor viralitas.
3. **Ringkasan otomatis.** Untuk video terpilih: transkrip (dari caption) → ringkasan LLM berisi topik, hook 3 detik pertama, struktur (hook → isi → CTA), dan gaya.
4. **Koleksi referensi.** Simpan, beri tag, dan catatan pribadi.
5. **Ekspor.** CSV/Markdown.
6. **Saran keyword.** Dari satu keyword awal, tampilkan variasi dari autocomplete YouTube, tag, dan kata yang sering muncul di judul video viral hasil pencarian.

### Fase 2 (P1) – integrasi Whop
1. Tarik data campaign dan bounty via Whop MCP/API (rate, budget, sisa budget, aturan konten, platform yang diizinkan).
2. Skor "Campaign Fit" = kecocokan keyword tren × rate × sisa budget × kompetisi.
3. Log klip yang diposting dan hasilnya (manual dulu, otomatis jika API mendukung).
4. Dashboard sederhana: earning per niche, per campaign, per bulan.
5. **Skor keyword** (lihat bagian 7A) dan penanda keyword yang cocok dengan niche campaign Whop.
6. **Analisis pola judul.** Dari Shorts viral hasil pencarian: panjang judul, kata pembuka, pola angka, pertanyaan atau klaim, penggunaan emoji dan hashtag.
7. **Generator judul & caption.** LLM membuat 5-10 opsi berdasarkan topik segmen, keyword target, dan pola judul terbukti. Pengguna memilih dan mengedit; tool tidak memposting otomatis.
8. **Cek syarat caption campaign.** Pengingat hashtag, mention, atau kata wajib sesuai aturan campaign.
9. **Riwayat judul.** Simpan judul yang dipakai beserta view hasilnya (terhubung ke `ClipLog`) untuk kalibrasi rekomendasi berikutnya.

### Fase 3 (P2)
- Alert lonjakan keyword.
- Analisis footage resmi campaign: transkrip, deteksi momen kuat, skor potensi.
- Analisis pola hook lintas video (kata pembuka, durasi hook, pola pertanyaan/klaim).

## 7. Skor Viralitas (spesifikasi awal)

Total view saja menyesatkan, jadi skor dinormalisasi:

```
velocity        = views / jam_sejak_upload
reach_ratio     = views / subscriber_channel   (dibatasi maksimum, hindari outlier)
engagement      = (likes + komentar) / views
viral_score     = 0.45·norm(velocity) + 0.30·norm(reach_ratio) + 0.25·norm(engagement)
```

- Normalisasi memakai persentil relatif terhadap hasil pencarian yang sama.
- Bobot bisa disetel di pengaturan dan akan dikalibrasi setelah ada data nyata.
- Video di bawah umur 3 jam diberi penalti kepercayaan (data belum stabil).

## 7A. Skor Keyword & Rekomendasi Judul (spesifikasi awal)

**Skor keyword** dihitung dari hasil pencarian keyword tersebut (sampel 30-50 Shorts terbaru):

```
demand        = median(velocity) dari video teratas
competition   = jumlah video ber-view tinggi ÷ total sampel  (semakin banyak, semakin jenuh)
freshness     = proporsi video viral yang diunggah dalam 7 hari terakhir
campaign_fit  = 1 jika cocok dengan niche campaign Whop aktif, selain itu 0
keyword_score = 0.40·norm(demand) + 0.25·(1 − competition) + 0.20·freshness + 0.15·campaign_fit
```

Keyword ditampilkan dengan label: **Peluang tinggi** (demand tinggi, kompetisi rendah), **Ramai** (demand tinggi, kompetisi tinggi), atau **Sepi**.

**Rekomendasi judul** bekerja dalam tiga langkah:
1. **Ekstraksi pola** dari judul Shorts viral: panjang (jumlah karakter/kata), tipe pembuka (pertanyaan, angka, klaim, cerita), emoji, hashtag.
2. **Generasi** opsi judul dan caption oleh LLM dengan masukan: ringkasan segmen klip, keyword target, pola dominan, serta aturan caption campaign.
3. **Pembelajaran** dari riwayat: pola judul yang menghasilkan view tertinggi pada klip pengguna diberi bobot lebih besar pada rekomendasi berikutnya.

**Catatan penting:** pola judul hanya berkorelasi dengan view dan tidak menjamin viral. Judul juga tidak boleh menyesatkan (clickbait yang tidak sesuai isi) atau melanggar aturan campaign. UI menampilkan dasar tiap rekomendasi (pola apa yang dipakai) agar pengguna bisa menilai sendiri.

## 8. Integrasi & Sumber Data

| Sumber | Kegunaan | Catatan |
|---|---|---|
| **YouTube Data API v3** | Pencarian, statistik video, info channel | Kuota default 10.000 unit/hari; `search.list` memakan 100 unit, jadi sekitar 100 pencarian/hari. Wajib cache hasil |
| **Caption/transkrip YouTube** | Bahan ringkasan | Tidak semua video punya caption; sediakan fallback "ringkasan berdasarkan judul + deskripsi" |
| **LLM (Claude API)** | Ringkasan, ekstraksi hook & struktur, generasi judul & caption | Output JSON terstruktur, cache per video |
| **YouTube autocomplete & tag video** | Saran keyword | Autocomplete tidak punya API resmi; gunakan tag dan judul dari YouTube Data API sebagai sumber utama, autocomplete sebagai tambahan opsional |
| **Whop MCP / API** | Campaign, bounty, submission, ledger | Perlu validasi (lihat Risiko R3) |

**Deteksi Shorts:** YouTube tidak menyediakan flag resmi. Pendekatan: filter durasi (≤ 3 menit), kata kunci `#shorts`, dan rasio vertikal jika tersedia.

## 9. Arsitektur (usulan)

```
[Web UI (Vite + React + TypeScript)]
       │
[Backend API (Node.js + Fastify/Express)]
   ├── YouTube Service  → cache (SQLite/Postgres + Redis opsional)
   ├── Scoring Service
   ├── Summarizer (LLM) → cache ringkasan
   ├── Whop Service (API/MCP)
   └── Collections / Tracker
       │
[Database: videos, keywords, summaries, collections, campaigns, submissions]
```

**Model data inti:** `Video`, `Channel`, `KeywordSearch`, `KeywordSuggestion` (keyword, skor, label), `Summary`, `Collection`, `Campaign`, `TitleOption` (opsi judul/caption, pola yang dipakai, dipilih atau tidak), `ClipLog` (video_id referensi, campaign_id, platform, url posting, judul final, view, earning).

**Stack (keputusan):**

| Lapisan | Pilihan |
|---|---|
| Frontend | Vite + React + TypeScript (SPA), TanStack Query untuk data fetching, Tailwind untuk styling |
| Backend | Node.js (TypeScript) dengan Fastify atau Express, berjalan sebagai API terpisah |
| Database | SQLite (`better-sqlite3`), cukup untuk pemakaian pribadi |
| Job/antrean | Antrean sederhana di proses Node (mis. `p-queue`); cron (`node-cron`) untuk alert fase 3 |
| Struktur repo | Monorepo dua folder: `web/` dan `server/`, tipe data dibagi lewat paket `shared/` |
| Konfigurasi | `.env` di `server/`; frontend hanya memanggil API backend |

Catatan: karena memakai Vite (SPA), semua panggilan ke YouTube, Whop, dan LLM harus lewat backend agar API key tidak terekspos di browser. Saat pengembangan, Vite proxy mengarahkan `/api` ke server Node. Deploy hanya perlu jika butuh alert 24 jam; jika di-host, cukup satu password sederhana atau binding ke localhost.

## 10. Persyaratan Non-Fungsional

- **Performa:** hasil pencarian tampil < 5 detik (dari cache < 1 detik); ringkasan < 20 detik per video.
- **Biaya:** batasi panggilan LLM (ringkas hanya video yang dipilih, cache permanen).
- **Keamanan:** API key di file `.env` (tidak di-commit ke Git), tidak pernah di client. Untuk Whop gunakan API key *read-only* pada MVP, bukan kredensial admin penuh.
- **Privasi:** hanya menyimpan metadata publik dan catatan pengguna.
- **Kepatuhan:** ikuti ToS YouTube API (batas penyimpanan data, tampilkan atribusi).

## 11. Risiko & Mitigasi

| ID | Risiko | Mitigasi |
|---|---|---|
| R1 | **Pelanggaran hak cipta / aturan campaign** jika hasil dipakai untuk repost | Tool tidak menyediakan unduhan; peringatan di UI; klip hanya dari footage resmi campaign |
| R2 | Kuota YouTube API cepat habis (±100 pencarian/hari) | Cache agresif, batasi pencarian, antrean. Untuk pemakaian pribadi kuota default umumnya cukup |
| R3 | Whop MCP/API kemungkinan berorientasi merchant dan belum tentu membuka daftar campaign Content Rewards publik | Validasi di Sprint 0; fallback input campaign manual atau salin dari halaman campaign |
| R4 | Skor viral tidak akurat | Bobot dapat disetel, kalibrasi dengan data nyata, tampilkan komponen skor secara transparan |
| R5 | Kompetisi clipper tinggi, budget campaign cepat habis | Fokus pada kecepatan: rekomendasi campaign dengan sisa budget + alert |
| R6 | Kredensial Whop ber-scope penuh | Pakai API key read-only; konfirmasi manual untuk aksi keuangan |
| R7 | Kualitas ringkasan buruk tanpa caption | Fallback berbasis judul/deskripsi + label "kepercayaan rendah" |
| R8 | Skor keyword bias karena sampel kecil dan biaya kuota (setiap pencarian memakan 100 unit) | Cache 24 jam, sampel terbatas, tampilkan jumlah sampel dan tingkat kepercayaan |
| R9 | Judul yang dihasilkan menyesatkan atau melanggar aturan campaign | Cek syarat caption campaign, pengguna selalu menyetujui manual, tampilkan dasar rekomendasi |

## 12. Metrik Keberhasilan

| Metrik | Target 60 hari setelah MVP |
|---|---|
| Waktu riset per campaign | Turun dari ±60 menit menjadi < 15 menit |
| Klip diposting per minggu | Naik minimal 2× |
| Rata-rata view per klip | Naik dibanding baseline sebelum memakai tool |
| Earning per jam kerja | Terlacak dan naik dari baseline |
| Akurasi skor viral (klip "tinggi" benar-benar performa baik) | > 60% |

## 13. Rencana & Milestone

| Fase | Durasi | Isi |
|---|---|---|
| Sprint 0 | 2–3 hari | Validasi akses Whop MCP (bounty, ledger), kuota YouTube, uji kualitas transkrip |
| MVP | 2–3 minggu | Pencarian, skor viral, ringkasan, koleksi, ekspor, saran keyword |
| Fase 2 | 3–4 minggu | Integrasi Whop, Campaign Fit, tracker hasil, skor keyword, analisis pola & generator judul, riwayat judul |
| Fase 3 | Menyesuaikan | Alert, analisis footage campaign, pola hook |

## 14. Pertanyaan Terbuka

1. Apakah Whop MCP bisa membaca daftar campaign/bounty Content Rewards publik, atau hanya milik akun sendiri?
2. ~~Pemakaian pribadi atau produk?~~ **Terjawab: pemakaian pribadi.**
3. Platform target posting: hanya YouTube Shorts, atau juga TikTok dan Instagram Reels?
4. Bahasa konten yang diriset: Indonesia, Inggris, atau keduanya?
5. Anggaran bulanan untuk API (YouTube kuota tambahan, LLM)?
6. Apakah judul dan caption dibuat dalam bahasa Indonesia, Inggris, atau mengikuti bahasa campaign?
7. Apakah generator judul perlu gaya khusus (santai, dramatis, edukatif) yang bisa dipilih per campaign?

## 15. Keputusan yang Dibutuhkan Berikutnya

- Setujui pendekatan "riset referensi, bukan repost".
- Pilih stack dan hosting (lokal dulu atau langsung cloud).
- Jalankan Sprint 0 untuk memvalidasi R2 dan R3 sebelum mulai membangun.
