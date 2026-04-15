// Gen 6+ type effectiveness chart
// effectiveness[attackingType][defendingType] = multiplier
export const TYPE_CHART: Record<string, Record<string, number>> = {
  normal:   { rock: 0.5, ghost: 0, steel: 0.5 },
  fire:     { fire: 0.5, water: 0.5, grass: 2, ice: 2, bug: 2, rock: 0.5, dragon: 0.5, steel: 2 },
  water:    { fire: 2, water: 0.5, grass: 0.5, ground: 2, rock: 2, dragon: 0.5 },
  electric: { water: 2, electric: 0.5, grass: 0.5, ground: 0, flying: 2, dragon: 0.5 },
  grass:    { fire: 0.5, water: 2, grass: 0.5, poison: 0.5, ground: 2, flying: 0.5, bug: 0.5, rock: 2, dragon: 0.5, steel: 0.5 },
  ice:      { fire: 0.5, water: 0.5, grass: 2, ice: 0.5, ground: 2, flying: 2, dragon: 2, steel: 0.5 },
  fighting: { normal: 2, ice: 2, poison: 0.5, flying: 0.5, psychic: 0.5, bug: 0.5, rock: 2, ghost: 0, dark: 2, steel: 2, fairy: 0.5 },
  poison:   { grass: 2, poison: 0.5, ground: 0.5, rock: 0.5, ghost: 0.5, steel: 0, fairy: 2 },
  ground:   { fire: 2, electric: 2, grass: 0.5, poison: 2, flying: 0, bug: 0.5, rock: 2, steel: 2 },
  flying:   { electric: 0.5, grass: 2, fighting: 2, bug: 2, rock: 0.5, steel: 0.5 },
  psychic:  { fighting: 2, poison: 2, psychic: 0.5, dark: 0, steel: 0.5 },
  bug:      { fire: 0.5, grass: 2, fighting: 0.5, flying: 0.5, psychic: 2, ghost: 0.5, dark: 2, steel: 0.5, fairy: 0.5 },
  rock:     { fire: 2, ice: 2, fighting: 0.5, ground: 0.5, flying: 2, bug: 2, steel: 0.5 },
  ghost:    { normal: 0, psychic: 2, ghost: 2, dark: 0.5 },
  dragon:   { dragon: 2, steel: 0.5, fairy: 0 },
  dark:     { fighting: 0.5, psychic: 2, ghost: 2, dark: 0.5, fairy: 0.5 },
  steel:    { fire: 0.5, water: 0.5, electric: 0.5, ice: 2, rock: 2, steel: 0.5, fairy: 2 },
  fairy:    { fire: 0.5, fighting: 2, poison: 0.5, dragon: 2, dark: 2, steel: 0.5 },
};

export const ALL_TYPES = [
  "normal","fire","water","electric","grass","ice","fighting","poison",
  "ground","flying","psychic","bug","rock","ghost","dragon","dark","steel","fairy",
];

export function getEffectiveness(attackType: string, defTypes: string[]): number {
  let mult = 1;
  for (const defType of defTypes) {
    const row = TYPE_CHART[attackType] ?? {};
    mult *= row[defType] ?? 1;
  }
  return mult;
}

export type CoverageResult = {
  type: string;
  multiplier: number;
};

/** For a team's offensive types, find best multiplier against each defending type combo */
export function getTeamOffensiveCoverage(
  teamTypes: string[][]
): Record<string, number> {
  const result: Record<string, number> = {};
  for (const defType of ALL_TYPES) {
    let best = 0;
    for (const pokemonTypes of teamTypes) {
      for (const atkType of pokemonTypes) {
        const eff = getEffectiveness(atkType, [defType]);
        if (eff > best) best = eff;
      }
    }
    result[defType] = best;
  }
  return result;
}

/** For a defending team's type combo, find weaknesses from all attack types */
export function getTeamDefensiveWeaknesses(
  teamDefTypes: string[][]
): Record<string, number[]> {
  // Returns: for each pokemon, map of attacker_type -> multiplier
  return Object.fromEntries(
    teamDefTypes.map((defTypes, i) => {
      const weaknesses: Record<string, number> = {};
      for (const atkType of ALL_TYPES) {
        weaknesses[atkType] = getEffectiveness(atkType, defTypes);
      }
      return [i.toString(), Object.values(weaknesses)];
    })
  );
}
