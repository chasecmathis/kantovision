export const GEN_RANGES = [
  { label: "Gen I",    start: 0,   count: 151 },
  { label: "Gen II",   start: 151, count: 100 },
  { label: "Gen III",  start: 251, count: 135 },
  { label: "Gen IV",   start: 386, count: 107 },
  { label: "Gen V",    start: 493, count: 156 },
  { label: "Gen VI",   start: 649, count: 72  },
  { label: "Gen VII",  start: 721, count: 88  },
  { label: "Gen VIII", start: 809, count: 96  },
  { label: "Gen IX",   start: 905, count: 120 },
] as const;

export type GenRange = (typeof GEN_RANGES)[number];

export const POKEDEX_PAGE_SIZE = 24; // 6-col grid × 4 rows
export const MODAL_PAGE_SIZE = 20;   // 5-col modal grid × 4 rows
