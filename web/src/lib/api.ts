import type {
  SearchRequest,
  SearchResponse,
  Summary,
  QuotaStatus,
  ApiError,
} from 'shared';

const BASE = '/api';

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ code: 'UNKNOWN', message: 'Terjadi kesalahan' })) as ApiError;
    throw new Error(errorBody.message || `HTTP ${res.status}`);
  }

  // Handle blob responses for export
  const contentType = res.headers.get('content-type') ?? '';
  if (contentType.includes('text/csv') || contentType.includes('text/markdown')) {
    const blob = await res.blob();
    return blob as unknown as T;
  }

  return res.json() as Promise<T>;
}

export async function searchVideos(request: SearchRequest): Promise<SearchResponse> {
  return apiFetch<SearchResponse>('/search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getSearchHistory(): Promise<{
  keyword: string;
  timeRange: string;
  language: string;
  maxDuration: number;
  resultCount: number;
  searchedAt: string;
}[]> {
  return apiFetch('/search/history');
}

export async function getSummary(videoId: string): Promise<Summary> {
  return apiFetch<Summary>('/summaries', {
    method: 'POST',
    body: JSON.stringify({ videoId }),
  });
}

export async function getQuota(): Promise<QuotaStatus> {
  return apiFetch<QuotaStatus>('/quota');
}

export async function getCollections(): Promise<{ id: number; name: string; description: string }[]> {
  return apiFetch('/collections');
}

export async function createCollection(name: string, description: string): Promise<{ id: number }> {
  return apiFetch('/collections', {
    method: 'POST',
    body: JSON.stringify({ name, description }),
  });
}

export async function addToCollection(
  collectionId: number,
  videoId: string,
  tags: string[],
  notes: string,
): Promise<void> {
  await apiFetch(`/collections/${collectionId}/items`, {
    method: 'POST',
    body: JSON.stringify({ videoId, tags, notes }),
  });
}

export async function getCollectionItems(collectionId: number): Promise<{
  id: number;
  collection_id: number;
  video_id: string;
  tags: string;
  notes: string;
  added_at: string;
  video_title: string;
  thumbnail_url: string;
  view_count: number;
  channel_title: string;
}[]> {
  return apiFetch(`/collections/${collectionId}/items`);
}

export async function removeFromCollection(collectionId: number, videoId: string): Promise<void> {
  await apiFetch(`/collections/${collectionId}/items/${videoId}`, {
    method: 'DELETE',
  });
}

export async function deleteCollection(collectionId: number): Promise<void> {
  await apiFetch(`/collections/${collectionId}`, {
    method: 'DELETE',
  });
}

export async function exportVideos(
  videoIds: string[],
  format: 'csv' | 'markdown',
  includeSummaries: boolean,
): Promise<Blob> {
  return apiFetch<Blob>('/export', {
    method: 'POST',
    body: JSON.stringify({ videoIds, format, includeSummaries }),
  });
}
