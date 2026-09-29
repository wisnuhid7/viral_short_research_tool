export const PROMPT_VERSION = 'v1.0';

/**
 * Build the summarization prompt for a YouTube Short.
 * Output: structured JSON with topic, hook, structure, style, and key moments.
 */
export function buildSummarizePrompt(
  title: string,
  description: string,
  transcript: string | null,
): { systemPrompt: string; userPrompt: string; sourceType: 'transcript' | 'title_description' } {
  const sourceType = transcript ? 'transcript' : 'title_description';

  const systemPrompt = `Kamu adalah analis konten YouTube Shorts yang ahli. Tugasmu adalah menganalisis video dan memberikan ringkasan terstruktur dalam format JSON.

ATURAN:
- Jawab HANYA dalam format JSON valid, tanpa teks tambahan di luar JSON.
- Semua nilai dalam bahasa Indonesia.
- Jangan mengarang fakta yang tidak ada di data.
- Jika data terbatas (hanya judul + deskripsi), tetap berikan analisis terbaik dari informasi yang tersedia.

FORMAT JSON:
{
  "topic": "Topik utama video dalam 1-2 kalimat",
  "hookFirst3Seconds": "Deskripsi apa yang terjadi di 3 detik pertama video (hook)",
  "structure": {
    "hook": "Bagaimana video membuka dan menarik perhatian",
    "body": "Isi utama dan alur cerita video",
    "cta": "Bagaimana video ditutup / call-to-action"
  },
  "style": "Gaya video (misalnya: cepat, dramatis, edukatif, lucu, storytelling, dll)",
  "keyMoments": ["Momen kunci 1", "Momen kunci 2", "..."]
}`;

  const contentSection = transcript
    ? `TRANSKRIP VIDEO:\n${transcript}`
    : `⚠️ Transkrip tidak tersedia. Analisis berdasarkan judul dan deskripsi saja.\n\nJUDUL: ${title}\n\nDESKRIPSI: ${description}`;

  const userPrompt = `Analisis YouTube Short berikut:

JUDUL: ${title}

DESKRIPSI: ${description}

${contentSection}

Berikan ringkasan terstruktur dalam format JSON sesuai aturan.`;

  return { systemPrompt, userPrompt, sourceType };
}
