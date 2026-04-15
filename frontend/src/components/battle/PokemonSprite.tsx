"use client";
import Image from "next/image";

interface PokemonSpriteProps {
  speciesId: number;
  name: string;
  fainted?: boolean;
  size?: number;
  flip?: boolean;
}

export function PokemonSprite({ speciesId, name, fainted = false, size = 160, flip = false }: PokemonSpriteProps) {
  const src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${speciesId}.png`;

  return (
    <div
      className="relative flex items-end justify-center transition-all duration-500"
      style={{
        width: size,
        height: size,
        opacity: fainted ? 0.25 : 1,
        filter: fainted ? "grayscale(1)" : "none",
        transform: `${flip ? "scaleX(-1)" : ""} ${fainted ? "translateY(12px)" : "translateY(0)"}`,
      }}
    >
      <Image
        src={src}
        alt={name}
        width={size}
        height={size}
        className="object-contain drop-shadow-lg"
        unoptimized
        priority
      />
    </div>
  );
}
