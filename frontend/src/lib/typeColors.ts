export const TYPE_COLORS: Record<string, string> = {
  normal: "#9CA3AF",
  fire: "#F97316",
  water: "#60A5FA",
  electric: "#FBBF24",
  grass: "#4ADE80",
  ice: "#67E8F9",
  fighting: "#EF4444",
  poison: "#C084FC",
  ground: "#D97706",
  flying: "#818CF8",
  psychic: "#F472B6",
  bug: "#84CC16",
  rock: "#A78BFA",
  ghost: "#7C3AED",
  dragon: "#6366F1",
  dark: "#78716C",
  steel: "#94A3B8",
  fairy: "#F9A8D4",
};

export const TYPE_BG: Record<string, string> = {
  normal: "rgba(156,163,175,0.15)",
  fire: "rgba(249,115,22,0.15)",
  water: "rgba(96,165,250,0.15)",
  electric: "rgba(251,191,36,0.15)",
  grass: "rgba(74,222,128,0.15)",
  ice: "rgba(103,232,249,0.15)",
  fighting: "rgba(239,68,68,0.15)",
  poison: "rgba(192,132,252,0.15)",
  ground: "rgba(217,119,6,0.15)",
  flying: "rgba(129,140,248,0.15)",
  psychic: "rgba(244,114,182,0.15)",
  bug: "rgba(132,204,22,0.15)",
  rock: "rgba(167,139,250,0.15)",
  ghost: "rgba(124,58,237,0.15)",
  dragon: "rgba(99,102,241,0.15)",
  dark: "rgba(120,113,108,0.15)",
  steel: "rgba(148,163,184,0.15)",
  fairy: "rgba(249,168,212,0.15)",
};

export const getTypeGradient = (types: string[]) => {
  if (types.length === 1) {
    const c = TYPE_COLORS[types[0]] ?? "#6c63ff";
    return `linear-gradient(135deg, ${c}20 0%, transparent 60%)`;
  }
  const c1 = TYPE_COLORS[types[0]] ?? "#6c63ff";
  const c2 = TYPE_COLORS[types[1]] ?? "#6c63ff";
  return `linear-gradient(135deg, ${c1}20 0%, ${c2}20 100%)`;
};
