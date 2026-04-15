import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTeams, createTeam, updateTeam, deleteTeam, type SavedTeam } from "@/src/lib/api";
import { fetchPokemon, type Team, type TeamMember } from "@/src/lib/pokeapi";
import { deserializeEvs, deserializeIvs, type SerializedSlot } from "@/src/lib/api";
import { useAuth } from "@/src/contexts/AuthContext";

export function useSavedTeams() {
  const { user } = useAuth();
  return useQuery<SavedTeam[]>({
    queryKey: ["saved-teams", user?.id],
    queryFn: fetchTeams,
    enabled: !!user,
    staleTime: 30_000,
  });
}

export function useCreateTeam() {
  const qc = useQueryClient();
  const { user } = useAuth();
  return useMutation({
    mutationFn: ({ name, team }: { name: string; team: Team }) => createTeam(name, team),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-teams", user?.id] }),
  });
}

export function useUpdateTeam() {
  const qc = useQueryClient();
  const { user } = useAuth();
  return useMutation({
    mutationFn: ({ id, name, team }: { id: string; name: string; team: Team }) =>
      updateTeam(id, name, team),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-teams", user?.id] }),
  });
}

export function useDeleteTeam() {
  const qc = useQueryClient();
  const { user } = useAuth();
  return useMutation({
    mutationFn: (id: string) => deleteTeam(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-teams", user?.id] }),
  });
}

// Hydrates a saved team's slots back into full TeamMember objects
export async function hydrateTeam(slots: (SerializedSlot | null)[]): Promise<Team> {
  return Promise.all(
    slots.map(async (slot): Promise<TeamMember | null> => {
      if (!slot) return null;
      const pokemon = await fetchPokemon(slot.pokemon_id);
      return {
        pokemon,
        abilityName: slot.ability,
        natureName: slot.nature,
        itemName: slot.item,
        moveNames: slot.move_names,
        evs: deserializeEvs(slot.evs),
        ivs: deserializeIvs(slot.ivs),
      };
    })
  );
}
