// ============================================================
// Elo Rating Calculation Module
// ============================================================

/** Default K-factor — controls how much a single match affects ratings */
const DEFAULT_K = 32;

/**
 * Calculate expected score for player A against player B.
 * Returns a value between 0 and 1 representing the probability
 * that player A will win.
 */
export function expectedScore(
  ratingA: number,
  ratingB: number,
): number {
  return 1 / (1 + Math.pow(10, (ratingB - ratingA) / 400));
}

/**
 * Calculate the new Elo ratings after a match.
 *
 * @param ratingA  - Current rating of player A
 * @param ratingB  - Current rating of player B
 * @param result   - Match result from A's perspective: 1 = win, 0.5 = draw, 0 = loss
 * @param k        - K-factor (default 32)
 * @returns Object with new ratings and the deltas for each player
 */
export function calculateNewRatings(
  ratingA: number,
  ratingB: number,
  result: number, // 1 (A wins), 0.5 (draw), 0 (A loses)
  k: number = DEFAULT_K,
): {
  newRatingA: number;
  newRatingB: number;
  deltaA: number;
  deltaB: number;
} {
  const expectedA = expectedScore(ratingA, ratingB);
  const expectedB = 1 - expectedA;

  const deltaA = Math.round(k * (result - expectedA));
  const deltaB = Math.round(k * (1 - result - expectedB));

  return {
    newRatingA: ratingA + deltaA,
    newRatingB: ratingB + deltaB,
    deltaA,
    deltaB,
  };
}

/**
 * Get a human-readable skill tier for a given Elo rating.
 */
export function getTier(elo: number): {
  name: string;
  color: string;
  min: number;
} {
  if (elo >= 2400) return { name: "Grandmaster", color: "#f59e0b", min: 2400 };
  if (elo >= 2200) return { name: "Master", color: "#a855f7", min: 2200 };
  if (elo >= 2000) return { name: "Diamond", color: "#06b6d4", min: 2000 };
  if (elo >= 1800) return { name: "Platinum", color: "#3b82f6", min: 1800 };
  if (elo >= 1600) return { name: "Gold", color: "#eab308", min: 1600 };
  if (elo >= 1400) return { name: "Silver", color: "#94a3b8", min: 1400 };
  return { name: "Bronze", color: "#b45309", min: 0 };
}

/**
 * Estimate how many matches it would take to reach a target rating
 * given a constant win rate. Useful for UI projections.
 */
export function matchesToTarget(
  currentElo: number,
  targetElo: number,
  winRate: number,
  avgOpponentElo: number = 1500,
  k: number = DEFAULT_K,
): number {
  if (winRate <= 0 || winRate >= 1) return Infinity;
  if (currentElo >= targetElo) return 0;

  const expected = expectedScore(currentElo, avgOpponentElo);
  const avgDelta = k * (winRate - expected);

  if (avgDelta <= 0) return Infinity;

  return Math.ceil((targetElo - currentElo) / avgDelta);
}
