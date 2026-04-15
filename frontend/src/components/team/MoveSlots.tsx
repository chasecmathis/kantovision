"use client";
import { useState } from "react";
import { MoveSlotRow } from "./MoveSlotRow";
import { MovePickerModal } from "./MovePickerModal";
import { type Pokemon } from "@/src/lib/pokeapi";

interface MoveSlotsProps {
  pokemon: Pokemon;
  moveNames: (string | null)[];
  onUpdate: (newMoveNames: (string | null)[]) => void;
}

export function MoveSlots({ pokemon, moveNames, onUpdate }: MoveSlotsProps) {
  const [openSlot, setOpenSlot] = useState<number | null>(null);

  const handleSelect = (moveName: string) => {
    if (openSlot === null) return;
    const next = [...moveNames];
    next[openSlot] = moveName;
    onUpdate(next);
    setOpenSlot(null);
  };

  const handleClear = (index: number) => {
    const next = [...moveNames];
    next[index] = null;
    onUpdate(next);
  };

  return (
    <>
      <div className="space-y-1.5">
        {moveNames.map((moveName, i) => (
          <MoveSlotRow
            key={i}
            moveName={moveName}
            slotIndex={i}
            onOpenPicker={() => setOpenSlot(i)}
            onClear={() => handleClear(i)}
          />
        ))}
      </div>

      {openSlot !== null && (
        <MovePickerModal
          pokemon={pokemon}
          currentMoveNames={moveNames}
          onSelect={handleSelect}
          onClose={() => setOpenSlot(null)}
        />
      )}
    </>
  );
}
