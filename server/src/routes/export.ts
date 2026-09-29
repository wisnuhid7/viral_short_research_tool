import { Router } from 'express';
import { exportRequestSchema } from 'shared';
import { ValidationError } from '../lib/errors.js';
import { getVideosByIds, getSummary } from '../db/queries.js';
import { PROMPT_VERSION } from '../services/prompts/summarize-video.js';

export const exportRouter = Router();

/** POST /api/export — export videos as CSV or Markdown */
exportRouter.post('/', (req, res, next) => {
  try {
    const parsed = exportRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError(
        `Input tidak valid: ${parsed.error.issues.map((i) => i.message).join(', ')}`
      );
    }

    const { videoIds, format, includeSummaries } = parsed.data;
    const videos = getVideosByIds(videoIds);

    if (videos.length === 0) {
      throw new ValidationError('Tidak ada video ditemukan untuk ID yang diberikan.');
    }

    if (format === 'csv') {
      const csv = generateCsv(videos, includeSummaries);
      res.setHeader('Content-Type', 'text/csv; charset=utf-8');
      res.setHeader('Content-Disposition', 'attachment; filename="shorts_research.csv"');
      res.send(csv);
    } else {
      const md = generateMarkdown(videos, includeSummaries);
      res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
      res.setHeader('Content-Disposition', 'attachment; filename="shorts_research.md"');
      res.send(md);
    }
  } catch (err) {
    next(err);
  }
});

function generateCsv(
  videos: { id: string; title: string; channelTitle: string; viewCount: number; likeCount: number; commentCount: number; publishedAt: string; duration: number }[],
  includeSummaries: boolean,
): string {
  const headers = ['ID', 'Judul', 'Channel', 'Views', 'Likes', 'Komentar', 'Durasi (detik)', 'Tanggal Upload'];
  if (includeSummaries) {
    headers.push('Topik', 'Hook', 'Gaya', 'Kepercayaan');
  }

  const rows = videos.map((v) => {
    const row = [
      v.id,
      escapeCsv(v.title),
      escapeCsv(v.channelTitle),
      String(v.viewCount),
      String(v.likeCount),
      String(v.commentCount),
      String(v.duration),
      v.publishedAt,
    ];

    if (includeSummaries) {
      const summary = getSummary(v.id, PROMPT_VERSION);
      if (summary) {
        row.push(
          escapeCsv(summary.topic),
          escapeCsv(summary.hookFirst3Seconds),
          escapeCsv(summary.style),
          summary.confidence,
        );
      } else {
        row.push('', '', '', '');
      }
    }

    return row.join(',');
  });

  return [headers.join(','), ...rows].join('\n');
}

function generateMarkdown(
  videos: { id: string; title: string; channelTitle: string; viewCount: number; likeCount: number; commentCount: number; publishedAt: string; duration: number }[],
  includeSummaries: boolean,
): string {
  let md = '# Hasil Riset YouTube Shorts\n\n';
  md += `Diekspor: ${new Date().toLocaleString('id-ID')}\n\n`;
  md += `Total: ${videos.length} video\n\n---\n\n`;

  for (const v of videos) {
    md += `## ${v.title}\n\n`;
    md += `- **Channel:** ${v.channelTitle}\n`;
    md += `- **Views:** ${v.viewCount.toLocaleString('id-ID')}\n`;
    md += `- **Likes:** ${v.likeCount.toLocaleString('id-ID')}\n`;
    md += `- **Komentar:** ${v.commentCount.toLocaleString('id-ID')}\n`;
    md += `- **Durasi:** ${v.duration} detik\n`;
    md += `- **Upload:** ${v.publishedAt}\n`;
    md += `- **Link:** https://youtube.com/shorts/${v.id}\n`;

    if (includeSummaries) {
      const summary = getSummary(v.id, PROMPT_VERSION);
      if (summary) {
        md += `\n### Ringkasan\n\n`;
        md += `- **Topik:** ${summary.topic}\n`;
        md += `- **Hook (3 detik pertama):** ${summary.hookFirst3Seconds}\n`;
        md += `- **Gaya:** ${summary.style}\n`;
        md += `- **Kepercayaan:** ${summary.confidence}\n`;
        md += `\n**Struktur:**\n`;
        md += `1. Hook: ${summary.structure.hook}\n`;
        md += `2. Isi: ${summary.structure.body}\n`;
        md += `3. CTA: ${summary.structure.cta}\n`;
      }
    }

    md += '\n---\n\n';
  }

  return md;
}

function escapeCsv(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}
