"""Clip feature tests: DB layer, pipeline, and HTTP routes.

yt-dlp / ffmpeg / Whisper / OpenAI are all monkeypatched — no network, no subprocess.
"""
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app.db import clip_queries as cq
from api.app.main import app
from api.app.services.clips import media, pipeline, select


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def clip_env(monkeypatch, tmp_path):
    """Patch every external step and record the calls."""
    calls: dict = {"download": [], "render": [], "srt": []}

    async def fake_download(url: str, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = dest_dir / "source.mp4"
        path.write_bytes(b"youtube-bytes")
        calls["download"].append(url)
        return path

    async def fake_probe(_path: Path) -> float:
        return 120.0

    async def fake_extract(_video: Path, out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"wav")
        return out_path

    async def fake_transcribe(_audio: Path) -> dict:
        return {
            "text": "Halo semuanya, ini momen terbaik.",
            "segments": [
                {"start": 10.0, "end": 15.0, "text": "Halo semuanya"},
                {"start": 20.0, "end": 25.0, "text": "ini momen terbaik"},
            ],
        }

    async def fake_select(_text: str, _duration: float) -> list[dict]:
        return [
            {"title": "Momen A", "reason": "hook kuat", "start": 10.0, "end": 40.0},
            {"title": "Momen B", "reason": "penutup", "start": 60.0, "end": 90.0},
        ]

    async def fake_render(
        input_path: Path,
        output_path: Path,
        start: float,
        end: float,
        mode: str,
        srt_path: Path | None = None,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"rendered-mp4")
        calls["render"].append(
            {"input": str(input_path), "start": start, "end": end, "mode": mode, "srt": str(srt_path)}
        )
        return output_path

    real_write_srt = media.write_srt

    def fake_write_srt(segments, clip_start, clip_end, out_path):
        real_write_srt(segments, clip_start, clip_end, out_path)
        calls["srt"].append(str(out_path))
        return out_path

    monkeypatch.setattr(media, "download_source", fake_download)
    monkeypatch.setattr(media, "probe_duration", fake_probe)
    monkeypatch.setattr(media, "extract_audio", fake_extract)
    monkeypatch.setattr(media, "render_clip", fake_render)
    monkeypatch.setattr(media, "write_srt", fake_write_srt)
    # Simulate an ffmpeg build that DOES support subtitles; the tests that check
    # the missing-filter path override this back to False.
    monkeypatch.setattr(media, "has_filter", lambda _name: True)
    monkeypatch.setattr(pipeline.transcribe, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(select, "select_moments", fake_select)
    monkeypatch.setattr(pipeline.select, "select_moments", fake_select)

    return calls


def _ready_source(client, tmp_path: Path, clip_env) -> dict:
    """Create a local source through the API and wait for the background task."""
    video = tmp_path / "source.mp4"
    video.write_bytes(b"local-bytes")
    r = client.post(
        "/api/clips/sources", json={"sourceType": "local", "sourceRef": str(video), "title": "Raw"}
    )
    assert r.status_code == 201
    return r.json()


# ─── DB layer ────────────────────────────────────────────


def test_clip_source_crud():
    source = cq.create_clip_source("local", "/tmp/a.mp4", "A")
    assert source["status"] == "pending"
    assert source["sourceType"] == "local"

    cq.update_clip_source(source["id"], status="ready", duration_seconds=42.5)
    fetched = cq.get_clip_source(source["id"])
    assert fetched["status"] == "ready"
    assert fetched["durationSeconds"] == 42.5

    assert [s["id"] for s in cq.list_clip_sources()] == [source["id"]]

    cq.delete_clip_source(source["id"])
    assert cq.get_clip_source(source["id"]) is None


def test_clip_crud_and_cascade():
    source = cq.create_clip_source("local", "/tmp/a.mp4")
    clip = cq.create_clip(source["id"], "Judul", 1.0, 21.0, mode="blur", subtitles=True)
    assert clip["mode"] == "blur"
    assert clip["subtitles"] is True
    assert clip["status"] == "pending"

    cq.update_clip(clip["id"], status="done", output_path="/tmp/clip.mp4")
    assert cq.get_clip(clip["id"])["status"] == "done"
    assert [c["id"] for c in cq.list_clips(source["id"])] == [clip["id"]]
    assert cq.list_clips(999) == []

    cq.delete_clip_source(source["id"])
    assert cq.get_clip(clip["id"]) is None


# ─── media helpers (pure) ────────────────────────────────


def test_build_render_command_crop_and_blur(tmp_path):
    inp, out = tmp_path / "in.mp4", tmp_path / "out.mp4"

    crop = media.build_render_command(inp, out, 5, 25, "crop")
    assert "-vf" in crop
    vf = crop[crop.index("-vf") + 1]
    assert "scale=1080:1920:force_original_aspect_ratio=increase" in vf
    assert "crop=1080:1920" in vf
    assert "-t" in crop and crop[crop.index("-t") + 1] == "20"

    blur = media.build_render_command(inp, out, 0, 30, "blur")
    assert "-filter_complex" in blur
    fc = blur[blur.index("-filter_complex") + 1]
    assert "boxblur" in fc and fc.endswith("[v]")
    assert blur[blur.index("-map") + 1] == "[v]"


def test_write_srt_clips_to_window(tmp_path):
    segments = [
        {"start": 0.0, "end": 5.0, "text": "sebelum"},
        {"start": 10.0, "end": 15.0, "text": "di dalam"},
        {"start": 40.0, "end": 50.0, "text": "setelah"},
    ]
    srt = media.write_srt(segments, 10.0, 20.0, tmp_path / "c.srt")
    content = srt.read_text(encoding="utf-8")
    assert "di dalam" in content
    assert "sebelum" not in content
    assert "setelah" not in content
    assert content.startswith("1\n00:00:00,000 --> 00:00:05,000")


def test_subtitle_filter_escapes_path(tmp_path):
    srt = tmp_path / "a:b.srt"
    cmd = media.build_render_command(tmp_path / "in.mp4", tmp_path / "out.mp4", 0, 10, "crop", srt)
    vf = cmd[cmd.index("-vf") + 1]
    assert "subtitles=filename='" in vf
    # Colons are escaped so ffmpeg's filter parser does not split on them.
    assert "a\\:b.srt" in vf


def test_render_rejects_missing_subtitles_filter(tmp_path, monkeypatch):
    """This ffmpeg build has no libass; requesting subtitles must fail clearly."""
    monkeypatch.setattr(media, "has_filter", lambda _name: False)
    monkeypatch.setattr(media, "ffmpeg_available", lambda: True)
    (tmp_path / "in.mp4").write_bytes(b"x")
    with pytest.raises(media.ClipToolingError) as err:
        asyncio.run(
            media.render_clip(tmp_path / "in.mp4", tmp_path / "out.mp4", 0, 5, "crop", tmp_path / "c.srt")
        )
    assert "libass" in str(err.value)


def test_select_clamp_rejects_invalid():
    assert select._clamp({"start": "x", "end": 5}, 100) is None
    assert select._clamp({"start": 0, "end": 2}, 100) is None  # shorter than MIN_CLIP_SECONDS
    clamped = select._clamp({"start": 0, "end": 500, "title": "T"}, 100)
    assert clamped["end"] == 100
    assert clamped["title"] == "T"


# ─── Local source pipeline ───────────────────────────────


def test_local_source_becomes_ready(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    assert source["status"] == "pending"

    fetched = client.get(f"/api/clips/sources/{source['id']}").json()
    assert fetched["status"] == "ready"
    assert fetched["durationSeconds"] == 120.0
    assert fetched["localPath"].endswith("source.mp4")
    assert fetched["transcriptPath"].endswith("transcript.json")


def test_youtube_source_downloads(client, clip_env):
    r = client.post(
        "/api/clips/sources",
        json={"sourceType": "youtube", "sourceRef": "https://youtube.com/watch?v=abc"},
    )
    assert r.status_code == 201
    assert clip_env["download"] == ["https://youtube.com/watch?v=abc"]

    fetched = client.get(f"/api/clips/sources/{r.json()['id']}").json()
    assert fetched["status"] == "ready"


def test_missing_local_file_sets_error(client, tmp_path, clip_env):
    r = client.post(
        "/api/clips/sources",
        json={"sourceType": "local", "sourceRef": str(tmp_path / "nope.mp4")},
    )
    assert r.status_code == 201
    fetched = client.get(f"/api/clips/sources/{r.json()['id']}").json()
    assert fetched["status"] == "error"
    assert "tidak ditemukan" in fetched["errorMessage"]


# ─── Clip creation & render ──────────────────────────────


def test_auto_clip_selects_first_moment_and_renders(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)

    r = client.post("/api/clips", json={"sourceId": source["id"]})
    assert r.status_code == 201
    clip = r.json()
    assert clip["title"] == "Momen A"
    assert clip["reason"] == "hook kuat"
    assert clip["startSeconds"] == 10.0
    assert clip["endSeconds"] == 40.0
    assert clip["mode"] == "crop"

    # Background render already ran (TestClient awaits background tasks).
    fetched = client.get(f"/api/clips/{clip['id']}").json()
    assert fetched["status"] == "done"
    assert fetched["outputPath"].endswith(f"clip_{clip['id']}.mp4")
    assert clip_env["render"][0]["mode"] == "crop"


def test_auto_clip_moment_index(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    r = client.post("/api/clips", json={"sourceId": source["id"], "momentIndex": 1, "mode": "blur"})
    assert r.status_code == 201
    assert r.json()["title"] == "Momen B"
    assert r.json()["mode"] == "blur"


def test_manual_window_clip(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    r = client.post("/api/clips", json={"sourceId": source["id"], "start": 5, "end": 35})
    assert r.status_code == 201
    clip = r.json()
    assert clip["title"] == "Klip manual"
    assert clip["startSeconds"] == 5.0
    assert clip["endSeconds"] == 35.0


def test_subtitles_writes_srt(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    r = client.post("/api/clips", json={"sourceId": source["id"], "start": 5, "end": 30, "subtitles": True})
    clip = r.json()
    assert clip["subtitles"] is True
    assert clip_env["srt"], "write_srt should have been called"
    assert clip_env["render"][0]["srt"].endswith(".srt")


def test_start_without_end_is_validation_error(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    r = client.post("/api/clips", json={"sourceId": source["id"], "start": 5})
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert "bersamaan" in r.json()["message"]


def test_clip_requires_ready_source(client, tmp_path, clip_env):
    pending = cq.create_clip_source("local", str(tmp_path / "a.mp4"))
    r = client.post("/api/clips", json={"sourceId": pending["id"]})
    assert r.status_code == 400
    assert "belum siap" in r.json()["message"]


def test_clip_unknown_source_404(client, clip_env):
    r = client.post("/api/clips", json={"sourceId": 9999})
    assert r.status_code == 404
    assert "tidak ditemukan" in r.json()["message"]


def test_render_failure_sets_clip_error(client, tmp_path, clip_env, monkeypatch):
    async def boom(*_a, **_k):
        raise media.ClipToolingError("ffmpeg mati")

    monkeypatch.setattr(media, "render_clip", boom)
    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post("/api/clips", json={"sourceId": source["id"]}).json()

    fetched = client.get(f"/api/clips/{clip['id']}").json()
    assert fetched["status"] == "error"
    assert "ffmpeg mati" in fetched["errorMessage"]


# ─── Download / delete / list ────────────────────────────


def test_download_ready_clip(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post("/api/clips", json={"sourceId": source["id"]}).json()

    r = client.get(f"/api/clips/{clip['id']}/download")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("video/mp4")
    assert r.content == b"rendered-mp4"


def test_download_pending_clip_404(client):
    source = cq.create_clip_source("local", "/tmp/a.mp4")
    clip = cq.create_clip(source["id"], "T", 0, 10)
    r = client.get(f"/api/clips/{clip['id']}/download")
    assert r.status_code == 404
    assert "belum tersedia" in r.json()["message"]


def test_list_clips_and_filter(client):
    s1 = cq.create_clip_source("local", "/tmp/a.mp4")
    s2 = cq.create_clip_source("local", "/tmp/b.mp4")
    c1 = cq.create_clip(s1["id"], "A", 0, 10)
    cq.create_clip(s2["id"], "B", 0, 10)

    assert {c["id"] for c in client.get("/api/clips").json()} == {c1["id"], cq.list_clips(s2["id"])[0]["id"]}
    only_s1 = client.get(f"/api/clips?sourceId={s1['id']}").json()
    assert [c["title"] for c in only_s1] == ["A"]


def test_delete_clip(client):
    source = cq.create_clip_source("local", "/tmp/a.mp4")
    clip = cq.create_clip(source["id"], "T", 0, 10)
    r = client.delete(f"/api/clips/{clip['id']}")
    assert r.status_code == 200
    assert cq.get_clip(clip["id"]) is None
    assert client.delete(f"/api/clips/{clip['id']}").status_code == 404


def test_delete_source_cascades_clips(client):
    source = cq.create_clip_source("local", "/tmp/a.mp4")
    clip = cq.create_clip(source["id"], "T", 0, 10)
    r = client.delete(f"/api/clips/sources/{source['id']}")
    assert r.status_code == 200
    assert cq.get_clip_source(source["id"]) is None
    assert cq.get_clip(clip["id"]) is None
    assert client.delete(f"/api/clips/sources/{source['id']}").status_code == 404


def test_delete_clip_removes_output_and_srt(client, tmp_path, clip_env):
    """Deleting a clip must remove both the mp4 and its burned-subtitle .srt."""
    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post(
        "/api/clips",
        json={"sourceId": source["id"], "start": 5, "end": 30, "subtitles": True},
    ).json()
    out = Path(client.get(f"/api/clips/{clip['id']}").json()["outputPath"])
    srt = out.with_suffix(".srt")
    assert out.is_file() and srt.is_file()

    assert client.delete(f"/api/clips/{clip['id']}").status_code == 200
    assert not out.exists() and not srt.exists()


def test_delete_source_removes_rendered_clip_files(client, tmp_path, clip_env):
    """Deleting a source must also clean up its rendered clips' media files."""
    from api.app.services.clips.pipeline import source_dir

    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post(
        "/api/clips", json={"sourceId": source["id"], "start": 1, "end": 10}
    ).json()
    out = Path(client.get(f"/api/clips/{clip['id']}").json()["outputPath"])
    assert out.is_file()

    assert client.delete(f"/api/clips/sources/{source['id']}").status_code == 200
    assert not out.exists()
    assert not source_dir(source["id"]).exists()


# ─── Validation ──────────────────────────────────────────


def test_create_source_validation(client):
    r = client.post("/api/clips/sources", json={})
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert r.json()["message"].startswith("Input tidak valid: ")


def test_create_source_invalid_type(client):
    r = client.post("/api/clips/sources", json={"sourceType": "vimeo", "sourceRef": "x"})
    assert r.status_code == 400
    assert "'youtube' | 'local'" in r.json()["message"]


def test_create_source_blank_ref(client):
    r = client.post("/api/clips/sources", json={"sourceType": "local", "sourceRef": ""})
    assert r.status_code == 400
    assert "at least 1 character" in r.json()["message"]


def test_create_clip_invalid_mode(client):
    r = client.post("/api/clips", json={"sourceId": 1, "mode": "stretch"})
    assert r.status_code == 400
    assert "'crop' | 'blur'" in r.json()["message"]


# ─── Explicit window validation (not silently re-clamped) ─


def test_manual_window_start_out_of_range_rejected(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)  # duration 120s
    r = client.post("/api/clips", json={"sourceId": source["id"], "start": 200, "end": 210})
    assert r.status_code == 400
    assert "di antara 0 dan 120" in r.json()["message"]


def test_manual_window_end_beyond_duration_rejected(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    r = client.post("/api/clips", json={"sourceId": source["id"], "start": 10, "end": 500})
    assert r.status_code == 400
    assert "melebihi durasi" in r.json()["message"]


def test_manual_window_below_minimum_rejected(client, tmp_path, clip_env):
    source = _ready_source(client, tmp_path, clip_env)
    r = client.post("/api/clips", json={"sourceId": source["id"], "start": 10, "end": 10.5})
    assert r.status_code == 400
    assert "minimal" in r.json()["message"]


def test_auto_moment_still_clamped(client, tmp_path, clip_env, monkeypatch):
    """Untrusted LLM moments are clamped, not rejected."""

    async def overshoot(_text, _duration):
        return [{"title": "Besar", "reason": "", "start": 100.0, "end": 999.0}]

    monkeypatch.setattr(select, "select_moments", overshoot)
    monkeypatch.setattr(pipeline.select, "select_moments", overshoot)
    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post("/api/clips", json={"sourceId": source["id"]}).json()
    assert clip["endSeconds"] == 120.0


# ─── Subtitles fallback policy ───────────────────────────


def test_subtitles_skipped_when_filter_missing(client, tmp_path, clip_env, monkeypatch):
    from api.app.config import settings

    monkeypatch.setattr(media, "has_filter", lambda _n: False)
    monkeypatch.setattr(settings, "clip_subtitles_fallback", "skip")
    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post(
        "/api/clips", json={"sourceId": source["id"], "start": 5, "end": 30, "subtitles": True}
    ).json()
    fetched = client.get(f"/api/clips/{clip['id']}").json()
    assert fetched["status"] == "done"
    assert clip_env["render"][0]["srt"] == "None"  # no .srt handed to ffmpeg
    assert not Path(fetched["outputPath"]).with_suffix(".srt").exists()


def test_subtitles_required_when_filter_missing(client, tmp_path, clip_env, monkeypatch):
    from api.app.config import settings

    monkeypatch.setattr(media, "has_filter", lambda _n: False)
    monkeypatch.setattr(settings, "clip_subtitles_fallback", "error")
    source = _ready_source(client, tmp_path, clip_env)
    clip = client.post(
        "/api/clips", json={"sourceId": source["id"], "start": 5, "end": 30, "subtitles": True}
    ).json()
    fetched = client.get(f"/api/clips/{clip['id']}").json()
    assert fetched["status"] == "error"
    assert "libass" in fetched["errorMessage"]


# ─── Subprocess timeout guard ────────────────────────────


def test_run_enforces_timeout():
    import sys

    with pytest.raises(media.ClipToolingError) as err:
        asyncio.run(media._run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.5))
    assert "batas waktu" in str(err.value)
