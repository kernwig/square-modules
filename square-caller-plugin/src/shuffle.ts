/**
 * Seeded shuffle. We shuffle the whole module list once on load (and on demand
 * via the re-shuffle button / `s` key), then always iterate in that fixed
 * order. Filtering just walks the shuffled order and keeps matches, so the
 * displayed options are effectively random but stable until re-shuffled. This
 * avoids per-display RNG work and makes repeats unlikely without extra tracking.
 */

/** Mulberry32: tiny, fast, deterministic PRNG from a 32-bit seed. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Fisher-Yates using the given rng; returns a new array, input untouched. */
export function shuffle<T>(items: readonly T[], rng: () => number): T[] {
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** A fresh random 32-bit seed. */
export function randomSeed(): number {
  return (Math.random() * 0x100000000) >>> 0;
}
