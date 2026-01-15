/**
 * Daily Cache Utility for Evidence and Timeline
 *
 * Features:
 * - Daily TTL (clears when date changes)
 * - Merge strategy (dedupe by bar_index)
 * - Max 100 items per cache
 */

import { Evidence, TimelineEvent } from './api';

const MAX_ITEMS = 100;

interface CachedEvidence {
  date: string;
  ticker: string;
  tf: string;
  items: Evidence[];
  lastUpdated: string;
}

interface CachedTimeline {
  date: string;
  ticker: string;
  tf: string;
  items: TimelineEvent[];
  lastUpdated: string;
}

// Get today's date in YYYY-MM-DD format
function getTodayDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

// Cache keys
function getEvidenceCacheKey(ticker: string, tf: string): string {
  return `klinelens:evidence:${ticker}:${tf}`;
}

function getTimelineCacheKey(ticker: string, tf: string): string {
  return `klinelens:timeline:${ticker}:${tf}`;
}

// ========== Evidence Cache ==========

export function loadCachedEvidence(ticker: string, tf: string): Evidence[] {
  try {
    const key = getEvidenceCacheKey(ticker, tf);
    const stored = localStorage.getItem(key);
    if (!stored) return [];

    const cached: CachedEvidence = JSON.parse(stored);

    // Check if date matches today
    if (cached.date !== getTodayDate()) {
      // Clear stale cache
      localStorage.removeItem(key);
      return [];
    }

    return cached.items || [];
  } catch {
    return [];
  }
}

export function saveCachedEvidence(ticker: string, tf: string, items: Evidence[]): void {
  try {
    const key = getEvidenceCacheKey(ticker, tf);
    const data: CachedEvidence = {
      date: getTodayDate(),
      ticker,
      tf,
      items: items.slice(0, MAX_ITEMS), // Limit to max items
      lastUpdated: new Date().toISOString(),
    };
    localStorage.setItem(key, JSON.stringify(data));
  } catch {
    // Storage quota exceeded or other error, silently fail
    console.warn('Failed to save evidence cache');
  }
}

export function mergeEvidence(cached: Evidence[], fresh: Evidence[]): Evidence[] {
  // Start with fresh items (they have priority)
  const merged = [...fresh];

  for (const item of cached) {
    // Only add cached items that don't conflict with fresh items
    // and have valid bar_time
    if (!item.bar_time) continue;  // Skip cached items without timestamp

    const exists = merged.some(
      e => e.bar_index === item.bar_index && e.type === item.type
    );
    if (!exists) {
      merged.push(item);
    }
  }

  // Sort by bar_index descending (newest first) and limit
  return merged
    .sort((a, b) => (b.bar_index || 0) - (a.bar_index || 0))
    .slice(0, MAX_ITEMS);
}

// ========== Timeline Cache ==========

export function loadCachedTimeline(ticker: string, tf: string): TimelineEvent[] {
  try {
    const key = getTimelineCacheKey(ticker, tf);
    const stored = localStorage.getItem(key);
    if (!stored) return [];

    const cached: CachedTimeline = JSON.parse(stored);

    // Check if date matches today
    if (cached.date !== getTodayDate()) {
      // Clear stale cache
      localStorage.removeItem(key);
      return [];
    }

    return cached.items || [];
  } catch {
    return [];
  }
}

export function saveCachedTimeline(ticker: string, tf: string, items: TimelineEvent[]): void {
  try {
    const key = getTimelineCacheKey(ticker, tf);
    const data: CachedTimeline = {
      date: getTodayDate(),
      ticker,
      tf,
      items: items.slice(0, MAX_ITEMS), // Limit to max items
      lastUpdated: new Date().toISOString(),
    };
    localStorage.setItem(key, JSON.stringify(data));
  } catch {
    // Storage quota exceeded or other error, silently fail
    console.warn('Failed to save timeline cache');
  }
}

export function mergeTimeline(cached: TimelineEvent[], fresh: TimelineEvent[]): TimelineEvent[] {
  // Start with fresh items (they have priority)
  const merged = [...fresh];

  for (const item of cached) {
    // Only add cached items that don't conflict with fresh items
    // and have valid timestamp
    if (!item.ts) continue;  // Skip cached items without timestamp

    const exists = merged.some(
      e => e.ts === item.ts && e.event_type === item.event_type
    );
    if (!exists) {
      merged.push(item);
    }
  }

  // Sort by timestamp descending (newest first) and limit
  return merged
    .sort((a, b) => new Date(b.ts || 0).getTime() - new Date(a.ts || 0).getTime())
    .slice(0, MAX_ITEMS);
}

// ========== Clear All Cache for Ticker ==========

export function clearCacheForTicker(ticker: string): void {
  const timeframes = ['1m', '5m', '1d'];
  for (const tf of timeframes) {
    try {
      localStorage.removeItem(getEvidenceCacheKey(ticker, tf));
      localStorage.removeItem(getTimelineCacheKey(ticker, tf));
    } catch {
      // Ignore errors
    }
  }
}
