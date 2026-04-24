import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMyProfile, createProfile, updateProfile, getBattleHistory, type ProfileData, type BattleHistoryItem } from "@/src/lib/api";
import { useAuth } from "@/src/contexts/AuthContext";

export function useMyProfile() {
  const { user } = useAuth();
  return useQuery<ProfileData | null>({
    queryKey: ["profile", user?.id],
    queryFn: getMyProfile,
    enabled: !!user,
    staleTime: 60_000,
    retry: false,
  });
}

export function useCreateProfile() {
  const qc = useQueryClient();
  const { user } = useAuth();
  return useMutation({
    mutationFn: ({ username, displayName }: { username: string; displayName?: string | null }) =>
      createProfile(username, displayName),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile", user?.id] }),
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  const { user } = useAuth();
  return useMutation({
    mutationFn: (displayName: string | null) => updateProfile(displayName),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile", user?.id] }),
  });
}

export function useBattleHistory() {
  const { user } = useAuth();
  return useQuery<BattleHistoryItem[]>({
    queryKey: ["battle-history", user?.id],
    queryFn: getBattleHistory,
    enabled: !!user,
    staleTime: 60_000,
  });
}
