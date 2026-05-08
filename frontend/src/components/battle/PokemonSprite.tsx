"use client";
import Image from "next/image";

interface PokemonSpriteProps {
  speciesId: number;
  name: string;
  fainted?: boolean;
  size?: number;
  flip?: boolean;
}

export function PokemonSprite({
  speciesId,
  name,
  fainted = false,
  size = 160,
  flip = false,
}: PokemonSpriteProps) {
  const src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${speciesId}.png`;

  // Vary animation timing per Pokemon so they don't bob in sync
  const floatDuration = 3 + (speciesId % 5) * 0.3;
  const floatDelay = (speciesId % 7) * 0.2;

  return (
    <div
      className="relative flex items-end justify-center"
      style={{ width: size, height: size }}
    >
      {/* Outer: handles flip + opacity/filter */}
      <div
        style={{
          transform: flip ? "scaleX(-1)" : undefined,
          transition: "opacity 0.5s ease, filter 0.5s ease",
          opacity: fainted ? 0.2 : 1,
          filter: fainted ? "grayscale(1) brightness(0.5)" : "none",
        }}
      >
        {/* Inner: idle float animation */}
        <div
          style={{
            animation: fainted
              ? "none"
              : `idleFloat ${floatDuration}s ease-in-out infinite`,
            animationDelay: `${floatDelay}s`,
            transform: fainted ? "translateY(12px)" : "translateY(0)",
            transition: fainted ? "transform 0.8s ease-in" : undefined,
          }}
        >
          <Image
            src={src}
            alt={name}
            width={size}
            height={size}
            className="object-contain"
            style={{
              filter: "drop-shadow(0 4px 16px rgba(0,0,0,0.45))",
            }}
            unoptimized
            priority
          />
        </div>
      </div>

      {/* Platform shadow — elliptical glow under sprite */}
      <div
        className="absolute left-1/2 -translate-x-1/2 pointer-events-none"
        style={{
          bottom: "-2px",
          width: "65%",
          height: "10px",
          background: fainted
            ? "radial-gradient(ellipse, rgba(248,113,113,0.08) 0%, transparent 70%)"
            : "radial-gradient(ellipse, rgba(108,99,255,0.14) 0%, transparent 70%)",
          borderRadius: "50%",
          transition: "opacity 0.5s",
          opacity: fainted ? 0.4 : 1,
        }}
      />
    </div>
  );
}
