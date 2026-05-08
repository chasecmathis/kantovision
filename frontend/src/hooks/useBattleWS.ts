"use client";
import { useCallback, useRef, useState } from "react";
import { supabase } from "@/src/lib/supabase";
import { fetchWsTicket } from "@/src/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface BattleMoveSlot {
  name: string;
  power: number;
  accuracy: number;
  max_pp: number;
  current_pp: number;
  type: string;
  category: "physical" | "special" | "status";
  priority: number;
  flags: string[];
}

export interface StatStages {
  attack: number;
  defense: number;
  special_attack: number;
  special_defense: number;
  speed: number;
  accuracy: number;
  evasion: number;
}

export interface BattlePokemon {
  species_id: number;
  name: string;
  current_hp: number;
  max_hp: number;
  attack: number;
  defense: number;
  special_attack: number;
  special_defense: number;
  speed: number;
  types: string[];
  moves: BattleMoveSlot[];
  fainted: boolean;
  ability: string;
  item: string;
  nature: string;
  status: string;
  stat_stages: StatStages;
  volatile_statuses: string[];
}

export interface BattlePlayerState {
  user_id: string;
  active_index: number;
  team: BattlePokemon[];
}

export interface FieldState {
  weather: string;
  weather_turns: number;
  terrain: string;
  terrain_turns: number;
  trick_room: number;
}

export interface SideState {
  stealth_rock: boolean;
  spikes: number;
  toxic_spikes: number;
  sticky_web: boolean;
  reflect: number;
  light_screen: number;
  tailwind: number;
}

export interface ClientBattleState {
  id: string;
  player1: BattlePlayerState;
  player2: BattlePlayerState;
  turn: number;
  status: "team_preview" | "active" | "ended";
  winner_id: string | null;
  log: string[];
  field: FieldState;
  side1: SideState;
  side2: SideState;
  awaiting_switch: string[];
}

export type BattleAction =
  | { type: "move"; move_index: number }
  | { type: "switch"; switch_to_index: number };

export type BattlePhase =
  | "idle"
  | "connecting"
  | "queued"
  | "matched"
  | "team_preview"
  | "active"
  | "ended";

export interface BattleEndInfo {
  winner_id: string | null;
  reason: "all_fainted" | "forfeit";
}

export interface ForcedSwitchOption {
  index: number;
  name: string;
  species_id: number;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useBattleWS() {
  const wsRef = useRef<WebSocket | null>(null);
  const intentionalRef = useRef(false);
  const reconnectAttempted = useRef(false);
  const pendingJoinRef = useRef<string | null>(null);

  const [phase, setPhase] = useState<BattlePhase>("idle");
  const phaseRef = useRef<BattlePhase>("idle");
  const [battleState, setBattleState] = useState<ClientBattleState | null>(null);
  const [battleId, setBattleId] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [myUserId, setMyUserId] = useState<string | null>(null);
  const [endInfo, setEndInfo] = useState<BattleEndInfo | null>(null);
  const [waitingForOpponent, setWaitingForOpponent] = useState(false);
  const [opponentDisconnected, setOpponentDisconnected] = useState(false);
  const [opponentDisconnectMessage, setOpponentDisconnectMessage] = useState<string>(
    "Opponent disconnected — waiting for reconnect..."
  );
  const [serverShuttingDown, setServerShuttingDown] = useState(false);
  const [turnStartedAt, setTurnStartedAt] = useState<number | null>(null);
  const [forcedSwitchOptions, setForcedSwitchOptions] = useState<ForcedSwitchOption[] | null>(null);

  // Keep a stable ref to battleId for use in closures
  const battleIdRef = useRef<string | null>(null);
  battleIdRef.current = battleId;

  function updatePhase(p: BattlePhase) {
    phaseRef.current = p;
    setPhase(p);
  }

  function handleMessage(msg: Record<string, unknown>) {
    switch (msg.type) {
      case "queue_joined":
        updatePhase("queued");
        setWaitingForOpponent(false);
        break;

      case "queue_left":
        updatePhase("idle");
        break;

      case "match_found":
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        updatePhase("matched");
        break;

      case "team_preview":
        setBattleState(msg.state as ClientBattleState);
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        updatePhase("team_preview");
        setWaitingForOpponent(false);
        break;

      case "battle_start":
        setBattleState(msg.state as ClientBattleState);
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        setLog((msg.state as ClientBattleState).log ?? []);
        setTurnStartedAt(typeof msg.turn_started_at === "number" ? msg.turn_started_at : null);
        updatePhase("active");
        setWaitingForOpponent(false);
        setForcedSwitchOptions(null);
        break;

      case "battle_resumed":
        setBattleState(msg.state as ClientBattleState);
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        setLog((msg.state as ClientBattleState).log ?? []);
        setTurnStartedAt(typeof msg.turn_started_at === "number" ? msg.turn_started_at : null);
        updatePhase("active");
        setOpponentDisconnected(false);
        break;

      case "opponent_disconnected":
        setOpponentDisconnected(true);
        if (typeof msg.message === "string") {
          setOpponentDisconnectMessage(msg.message);
        }
        break;

      case "opponent_reconnected":
        setOpponentDisconnected(false);
        break;

      case "move_received":
        if (myUserId == msg.user_id) setWaitingForOpponent(true);
        break;

      case "turn_result":
        setBattleState(msg.state as ClientBattleState);
        setLog((prev) => [...prev, ...(msg.log as string[])]);
        setTurnStartedAt(typeof msg.turn_started_at === "number" ? msg.turn_started_at : null);
        setWaitingForOpponent(false);
        break;

      case "forced_switch":
        setForcedSwitchOptions(msg.available as ForcedSwitchOption[]);
        setWaitingForOpponent(false);
        break;

      case "battle_end":
        setEndInfo({ winner_id: msg.winner_id as string | null, reason: msg.reason as "all_fainted" | "forfeit" });
        updatePhase("ended");
        setForcedSwitchOptions(null);
        break;

      case "server_shutdown":
        setServerShuttingDown(true);
        break;

      case "error":
        console.warn("[BattleWS] Server error:", msg.message);
        break;
    }
  }

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    updatePhase("connecting");
    intentionalRef.current = false;
    reconnectAttempted.current = false;

    const { data } = await supabase.auth.getSession();
    const userId = data.session?.user?.id ?? null;

    if (!userId) {
      updatePhase("idle");
      return;
    }

    setMyUserId(userId);

    let ticket: string;
    try {
      const result = await fetchWsTicket();
      ticket = result.ticket;
    } catch {
      updatePhase("idle");
      return;
    }

    const wsBase = process.env.NEXT_PUBLIC_API_WS_URL ?? "ws://localhost:8000";
    const ws = new WebSocket(`${wsBase}/ws/battle?ticket=${encodeURIComponent(ticket)}`);
    wsRef.current = ws;

    ws.onopen = () => {
      updatePhase("idle");
      reconnectAttempted.current = false;
      if (pendingJoinRef.current) {
        ws.send(JSON.stringify({ type: "join_queue", team_id: pendingJoinRef.current }));
        pendingJoinRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        handleMessage(JSON.parse(event.data as string));
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (!intentionalRef.current && !reconnectAttempted.current) {
        reconnectAttempted.current = true;
        setTimeout(() => connect(), 2500);
      } else {
        updatePhase("idle");
      }
    };

    ws.onerror = () => ws.close();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const joinQueue = useCallback((teamId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "join_queue", team_id: teamId }));
    } else {
      pendingJoinRef.current = teamId;
      connect();
    }
  }, [connect]); // eslint-disable-line react-hooks/exhaustive-deps

  const leaveQueue = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: "leave_queue" }));
  }, []);

  const selectLead = useCallback((leadIndex: number) => {
    const bid = battleIdRef.current;
    if (!bid) return;
    wsRef.current?.send(JSON.stringify({ type: "select_lead", battle_id: bid, lead_index: leadIndex }));
    setWaitingForOpponent(true);
  }, []);

  const makeAction = useCallback((action: BattleAction) => {
    const bid = battleIdRef.current;
    if (!bid) return;
    wsRef.current?.send(JSON.stringify({ type: "make_action", battle_id: bid, action }));
    setWaitingForOpponent(true);
  }, []);

  const makeMove = useCallback((moveIndex: number) => {
    makeAction({ type: "move", move_index: moveIndex });
  }, [makeAction]);

  const switchPokemon = useCallback((switchToIndex: number) => {
    makeAction({ type: "switch", switch_to_index: switchToIndex });
  }, [makeAction]);

  const submitSwitch = useCallback((switchToIndex: number) => {
    const bid = battleIdRef.current;
    if (!bid) return;
    wsRef.current?.send(JSON.stringify({ type: "submit_switch", battle_id: bid, switch_to_index: switchToIndex }));
    setForcedSwitchOptions(null);
    setWaitingForOpponent(true);
  }, []);

  const forfeit = useCallback(() => {
    const bid = battleIdRef.current;
    if (!bid) return;
    intentionalRef.current = true;
    wsRef.current?.send(JSON.stringify({ type: "forfeit", battle_id: bid }));
  }, []);

  const disconnect = useCallback(() => {
    intentionalRef.current = true;
    pendingJoinRef.current = null;
    if (phaseRef.current === "queued") {
      wsRef.current?.send(JSON.stringify({ type: "leave_queue" }));
    }
    wsRef.current?.close();
    updatePhase("idle");
    setBattleState(null);
    setBattleId(null);
    battleIdRef.current = null;
    setLog([]);
    setEndInfo(null);
    setWaitingForOpponent(false);
    setOpponentDisconnected(false);
    setServerShuttingDown(false);
    setTurnStartedAt(null);
    setForcedSwitchOptions(null);
  }, []);

  return {
    phase,
    battleState,
    battleId,
    log,
    myUserId,
    endInfo,
    waitingForOpponent,
    opponentDisconnected,
    opponentDisconnectMessage,
    serverShuttingDown,
    turnStartedAt,
    forcedSwitchOptions,
    connect,
    joinQueue,
    leaveQueue,
    selectLead,
    makeMove,
    makeAction,
    switchPokemon,
    submitSwitch,
    forfeit,
    disconnect,
  };
}
