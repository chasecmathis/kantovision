"use client";
import { useQuery } from "@tanstack/react-query";
import {
  fetchPokemon,
  fetchPokemonList,
  fetchPokemonSpecies,
  fetchEvolutionChain,
  fetchMove,
  fetchNatureList,
  fetchItemList,
  fetchItem,
  fetchAbility,
} from "@/src/lib/pokeapi";

export function usePokemonList(limit = 151, offset = 0) {
  return useQuery({
    queryKey: ["pokemon-list", limit, offset],
    queryFn: () => fetchPokemonList(limit, offset),
  });
}

export function usePokemon(nameOrId: string | number) {
  return useQuery({
    queryKey: ["pokemon", nameOrId],
    queryFn: () => fetchPokemon(nameOrId),
    enabled: !!nameOrId,
  });
}

export function usePokemonSpecies(nameOrId: string | number) {
  return useQuery({
    queryKey: ["pokemon-species", nameOrId],
    queryFn: () => fetchPokemonSpecies(nameOrId),
    enabled: !!nameOrId,
  });
}

export function usePokemonWithSpecies(nameOrId: string | number) {
  const pokemon = usePokemon(nameOrId);
  const species = usePokemonSpecies(nameOrId);
  return { pokemon, species };
}

export function useEvolutionChain(url: string | undefined) {
  return useQuery({
    queryKey: ["evolution-chain", url],
    queryFn: () => fetchEvolutionChain(url!),
    enabled: !!url,
  });
}

export function useMove(name: string | null | undefined) {
  return useQuery({
    queryKey: ["move", name],
    queryFn: () => fetchMove(name!),
    enabled: !!name,
    staleTime: Infinity,
  });
}

export function useNatureList() {
  return useQuery({
    queryKey: ["nature-list"],
    queryFn: fetchNatureList,
    staleTime: Infinity,
  });
}

export function useItemList() {
  return useQuery({
    queryKey: ["item-list"],
    queryFn: () => fetchItemList(2175),
    staleTime: Infinity,
  });
}

export function useItem(name: string | null | undefined) {
  return useQuery({
    queryKey: ["item", name],
    queryFn: () => fetchItem(name!),
    enabled: !!name,
    staleTime: Infinity,
  });
}

export function useAbility(name: string | null | undefined) {
  return useQuery({
    queryKey: ["ability", name],
    queryFn: () => fetchAbility(name!),
    enabled: !!name,
    staleTime: Infinity,
  });
}

export function useTeamMemberMoves(moveNames: (string | null)[]) {
  const m0 = useMove(moveNames[0]);
  const m1 = useMove(moveNames[1]);
  const m2 = useMove(moveNames[2]);
  const m3 = useMove(moveNames[3]);
  return [m0, m1, m2, m3] as const;
}
