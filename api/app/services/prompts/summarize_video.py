"""Summarization prompt builder.

Port of server/src/services/prompts/summarize-video.ts.
"""

PROMPT_VERSION = "v1.0"

SYSTEM_PROMPT = """Kamu adalah analis konten YouTube Shorts yang ahli. Tugasmu adalah menganalisis video dan memberikan ringkasan terstruktur dalam format JSON.

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
}"""


def build_summarize_prompt(
    title: str,
    description: str,
    transcript: str | None,
) -> dict:
    """Build the summarization prompt for a YouTube Short.

    Returns a dict with `systemPrompt`, `userPrompt`, and `sourceType`.
    """
    source_type = "transcript" if transcript else "title_description"

    if transcript:
        content_section = f"TRANSKRIP VIDEO:\n{transcript}"
    else:
        content_section = (
            "⚠️ Transkrip tidak tersedia. Analisis berdasarkan judul dan deskripsi saja."
            f"\n\nJUDUL: {title}\n\nDESKRIPSI: {description}"
        )

    user_prompt = (
        "Analisis YouTube Short berikut:\n\n"
        f"JUDUL: {title}\n\n"
        f"DESKRIPSI: {description}\n\n"
        f"{content_section}\n\n"
        "Berikan ringkasan terstruktur dalam format JSON sesuai aturan."
    )

    return {
        "systemPrompt": SYSTEM_PROMPT,
        "userPrompt": user_prompt,
        "sourceType": source_type,
    }
