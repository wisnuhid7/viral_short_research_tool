"""Pydantic models mirroring shared/src/index.ts.

Field names stay camelCase so JSON in/out matches the TS API exactly.
Request models enforce the same constraints as the zod schemas; domain/response
models are intentionally relaxed (the TS versions were compile-time types).
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TimeRange = Literal["24h", "7d", "30d"]
ExportFormat = Literal["csv", "markdown"]
CampaignCategory = Literal[
    "all",
    "ai_tech",
    "finance_crypto",
    "gaming",
    "business_sidehustle",
    "fitness_lifestyle",
    "entertainment",
    "other",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ─── Domain ──────────────────────────────────────────────


class Channel(_Base):
    id: str
    title: str
    subscriberCount: int
    thumbnailUrl: str | None = None
    fetchedAt: str


class Video(_Base):
    id: str
    title: str
    description: str
    channelId: str
    channelTitle: str
    publishedAt: str
    thumbnailUrl: str
    duration: int
    viewCount: int
    likeCount: int
    commentCount: int
    tags: list[str] = Field(default_factory=list)
    isShort: bool
    fetchedAt: str


class ViralScore(_Base):
    videoId: str
    velocity: float
    velocityNorm: float
    reachRatio: float
    reachRatioNorm: float
    engagement: float
    engagementNorm: float
    totalScore: float
    confidencePenalty: bool
    sampleSize: int


class VideoWithScore(Video):
    viralScore: ViralScore
    subscriberCount: int | None = None


class SummaryStructure(_Base):
    hook: str
    body: str
    cta: str


class Summary(_Base):
    videoId: str
    topic: str
    hookFirst3Seconds: str
    structure: SummaryStructure
    style: str
    keyMoments: list[str] = Field(default_factory=list)
    confidence: Literal["high", "low"]
    sourceType: Literal["transcript", "title_description"]
    promptVersion: str
    createdAt: str


class KeywordSuggestion(_Base):
    keyword: str
    source: Literal["tag", "title_word", "autocomplete"]
    frequency: int
    parentKeyword: str


class Campaign(_Base):
    id: str
    name: str
    creatorOrBrand: str
    category: CampaignCategory = "other"
    url: str = ""
    ratePerKViews: float
    totalBudget: float
    remainingBudget: float
    deadline: str | None = None
    requiredHashtags: list[str] = Field(default_factory=list)
    requiredMentions: list[str] = Field(default_factory=list)
    allowedPlatforms: list[str] = Field(default_factory=lambda: ["YouTube Shorts"])
    targetKeywords: list[str] = Field(default_factory=list)
    notes: str = ""
    spotsRemaining: float | None = None
    isWhopLive: bool = False
    whopGoalType: str | None = None
    createdAt: str
    updatedAt: str


class EarningProjection(_Base):
    views10k: float
    views50k: float
    views100k: float
    views500k: float


class ViewsNeededForTarget(_Base):
    for25USD: float
    for50USD: float
    for100USD: float


class NicheVirality(_Base):
    score: float
    label: str
    audienceSize: str


class CampaignRating(_Base):
    campaignId: str
    tier: Literal["S", "A", "B", "C"]
    opportunityScore: float
    earningScore: float
    demandScore: float
    budgetScore: float
    projectedEarnings: EarningProjection
    budgetHealth: Literal["safe", "moderate", "low"]
    verdict: str
    targetEaseLevel: Literal["very_easy", "easy", "moderate", "hard"]
    targetEaseScore: float
    viewsNeededForTarget: ViewsNeededForTarget
    nicheVirality: NicheVirality
    budgetSafetyPockets: float
    easeExplanation: str
    strategyTips: list[str]


class CampaignWithRating(Campaign):
    rating: CampaignRating


# ─── Requests ────────────────────────────────────────────


class SearchRequest(_Base):
    keyword: str = Field(min_length=1, max_length=200)
    timeRange: TimeRange = "7d"
    language: str = "any"
    maxDuration: int = Field(default=180, ge=1, le=180)
    minViews: int = Field(default=0, ge=0)


class SummaryRequest(_Base):
    videoId: str = Field(min_length=1)


class CreateCollectionRequest(_Base):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class AddToCollectionRequest(_Base):
    videoId: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class ExportRequest(_Base):
    videoIds: list[str] = Field(min_length=1)
    format: ExportFormat
    includeSummaries: bool = False


class CreateCampaignRequest(_Base):
    name: str = Field(min_length=1)
    creatorOrBrand: str = Field(min_length=1)
    category: CampaignCategory = "other"
    url: str = ""
    ratePerKViews: float = Field(gt=0)
    totalBudget: float = Field(gt=0)
    remainingBudget: float = Field(ge=0)
    deadline: str | None = None
    requiredHashtags: list[str] = Field(default_factory=list)
    requiredMentions: list[str] = Field(default_factory=list)
    allowedPlatforms: list[str] = Field(default_factory=lambda: ["YouTube Shorts"])
    targetKeywords: list[str] = Field(default_factory=list)
    notes: str = ""


# ─── Responses ───────────────────────────────────────────


class SearchResponse(_Base):
    keyword: str
    videos: list[VideoWithScore]
    suggestions: list[KeywordSuggestion]
    quotaUsed: int
    quotaRemaining: int
    cachedAt: str | None = None


class QuotaStatus(_Base):
    used: int
    limit: int
    remaining: int
    resetsAt: str


class ApiError(_Base):
    code: str
    message: str


class WhopSyncStatus(_Base):
    lastSyncedAt: str | None = None
    campaignsCount: float
    status: Literal["idle", "syncing", "success", "error"]
    errorMessage: str | None = None


class WhopSyncResponse(_Base):
    success: bool
    count: float
    syncedAt: str
    message: str


# ─── Clips ───────────────────────────────────────────────

ClipSourceType = Literal["youtube", "local"]
ClipSourceStatus = Literal["pending", "downloading", "transcribing", "ready", "error"]
ClipStatus = Literal["pending", "rendering", "done", "error"]
ClipRenderMode = Literal["crop", "blur"]


class ClipSource(_Base):
    id: int
    sourceType: ClipSourceType
    sourceRef: str
    title: str | None = None
    durationSeconds: float | None = None
    localPath: str | None = None
    transcriptPath: str | None = None
    status: ClipSourceStatus
    errorMessage: str | None = None
    createdAt: str
    updatedAt: str


class Clip(_Base):
    id: int
    sourceId: int
    title: str
    reason: str | None = None
    startSeconds: float
    endSeconds: float
    mode: ClipRenderMode
    subtitles: bool
    status: ClipStatus
    outputPath: str | None = None
    errorMessage: str | None = None
    createdAt: str
    updatedAt: str


class CreateClipSourceRequest(_Base):
    sourceType: ClipSourceType
    sourceRef: str = Field(min_length=1)
    title: str | None = None


class CreateClipRequest(_Base):
    sourceId: int = Field(gt=0)
    start: float | None = Field(default=None, ge=0)
    end: float | None = Field(default=None, gt=0)
    mode: ClipRenderMode = "crop"
    subtitles: bool = False
    title: str | None = None
    momentIndex: int = Field(default=0, ge=0)