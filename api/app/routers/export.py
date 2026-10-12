"""Export route — port of server/src/routes/export.ts."""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Response

from api.app.db.queries import get_summary, get_videos_by_ids
from api.app.errors import ValidationError
from api.app.lib.format import to_id_string
from api.app.lib.validation import parse_body
from api.app.schemas import ExportRequest
from api.app.services.prompts.summarize_video import PROMPT_VERSION

router = APIRouter()


def escape_csv(value: str) -> str:
    if "," in value or '"' in value or "\n" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


def _id_datetime(date: datetime) -> str:
    """Approximate `new Date().toLocaleString('id-ID')`."""
    return (
        f"{date.day:02d}/{date.month:02d}/{date.year}, "
        f"{date.hour:02d}.{date.minute:02d}.{date.second:02d}"
    )


def generate_csv(videos: list[dict], include_summaries: bool) -> str:
    headers = ["ID", "Judul", "Channel", "Views", "Likes", "Komentar", "Durasi (detik)", "Tanggal Upload"]
    if include_summaries:
        headers.extend(["Topik", "Hook", "Gaya", "Kepercayaan"])

    rows = []
    for v in videos:
        row = [
            v["id"],
            escape_csv(v["title"]),
            escape_csv(v["channelTitle"]),
            str(v["viewCount"]),
            str(v["likeCount"]),
            str(v["commentCount"]),
            str(v["duration"]),
            v["publishedAt"],
        ]

        if include_summaries:
            summary = get_summary(v["id"], PROMPT_VERSION)
            if summary:
                row.extend(
                    [
                        escape_csv(summary["topic"]),
                        escape_csv(summary["hookFirst3Seconds"]),
                        escape_csv(summary["style"]),
                        summary["confidence"],
                    ]
                )
            else:
                row.extend(["", "", "", ""])

        rows.append(",".join(row))

    return "\n".join([",".join(headers), *rows])


def generate_markdown(videos: list[dict], include_summaries: bool) -> str:
    md = "# Hasil Riset YouTube Shorts\n\n"
    md += f"Diekspor: {_id_datetime(datetime.now())}\n\n"
    md += f"Total: {len(videos)} video\n\n---\n\n"

    for v in videos:
        md += f"## {v['title']}\n\n"
        md += f"- **Channel:** {v['channelTitle']}\n"
        md += f"- **Views:** {to_id_string(v['viewCount'])}\n"
        md += f"- **Likes:** {to_id_string(v['likeCount'])}\n"
        md += f"- **Komentar:** {to_id_string(v['commentCount'])}\n"
        md += f"- **Durasi:** {v['duration']} detik\n"
        md += f"- **Upload:** {v['publishedAt']}\n"
        md += f"- **Link:** https://youtube.com/shorts/{v['id']}\n"

        if include_summaries:
            summary = get_summary(v["id"], PROMPT_VERSION)
            if summary:
                md += "\n### Ringkasan\n\n"
                md += f"- **Topik:** {summary['topic']}\n"
                md += f"- **Hook (3 detik pertama):** {summary['hookFirst3Seconds']}\n"
                md += f"- **Gaya:** {summary['style']}\n"
                md += f"- **Kepercayaan:** {summary['confidence']}\n"
                md += "\n**Struktur:**\n"
                md += f"1. Hook: {summary['structure']['hook']}\n"
                md += f"2. Isi: {summary['structure']['body']}\n"
                md += f"3. CTA: {summary['structure']['cta']}\n"

        md += "\n---\n\n"

    return md


@router.post("")
@router.post("/", include_in_schema=False)
def export(body: Any = Body(default=None)):
    parsed: ExportRequest = parse_body(ExportRequest, body)  # type: ignore[assignment]
    videos = get_videos_by_ids(parsed.videoIds)

    if len(videos) == 0:
        raise ValidationError("Tidak ada video ditemukan untuk ID yang diberikan.")

    if parsed.format == "csv":
        csv = generate_csv(videos, parsed.includeSummaries)
        return Response(
            content=csv,
            headers={
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": 'attachment; filename="shorts_research.csv"',
            },
        )

    md = generate_markdown(videos, parsed.includeSummaries)
    return Response(
        content=md,
        headers={
            "Content-Type": "text/markdown; charset=utf-8",
            "Content-Disposition": 'attachment; filename="shorts_research.md"',
        },
    )
