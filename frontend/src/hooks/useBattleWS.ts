"use client";
import { useCallback, useRef, useState } from "react";
import { supabase } from "@/src/lib/supabase";
import { fetchWsTicket } from "@/src/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface BattleMoveSlot {
  name: string;
  power: number;
  accuracy: number;
  pp: number;
  type: string;
  category: "physical" | "special" | "status";
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
}

export interface BattlePlayerState {
  user_id: string;
  active_index: number;
  team: BattlePokemon[];
}

export interface ClientBattleState {
  id: string;
  player1: BattlePlayerState;
  player2: BattlePlayerState;
  turn: number;
  status: "active" | "ended";
  winner_id: string | null;
  log: string[];
}

export type BattlePhase = "idle" | "connecting" | "queued" | "matched" | "active" | "ended";

export interface BattleEndInfo {
  winner_id: string | null;
  reason: "all_fainted" | "forfeit";
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useBattleWS() {
  const wsRef = useRef<WebSocket | null>(null);
  const intentionalRef = useRef(false);
  const reconnectAttempted = useRef(false);

  const [phase, setPhase] = useState<BattlePhase>("idle");
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

  // Keep a stable ref to battleId for use in closures
  const battleIdRef = useRef<string | null>(null);
  battleIdRef.current = battleId;

  function handleMessage(msg: Record<string, unknown>) {
    switch (msg.type) {
      case "queue_joined":
        setPhase("queued");
        setWaitingForOpponent(false);
        break;

      case "queue_left":
        setPhase("idle");
        break;

      case "match_found":
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        setPhase("matched");
        break;

      case "battle_start":
        setBattleState(msg.state as ClientBattleState);
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        setLog((msg.state as ClientBattleState).log ?? []);
        setPhase("active");
        setWaitingForOpponent(false);
        break;

      case "battle_resumed":
        setBattleState(msg.state as ClientBattleState);
        setBattleId(msg.battle_id as string);
        battleIdRef.current = msg.battle_id as string;
        setLog((msg.state as ClientBattleState).log ?? []);
        setPhase("active");
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
        // The other player submitted their move; we're waiting on ourselves or them
        if (myUserId == msg.user_id) setWaitingForOpponent(true);
        break;

      case "turn_result":
        setBattleState(msg.state as ClientBattleState);
        setLog((prev) => [...prev, ...(msg.log as string[])]);
        setWaitingForOpponent(false);
        break;

      case "battle_end":
        setEndInfo({ winner_id: msg.winner_id as string | null, reason: msg.reason as "all_fainted" | "forfeit" });
        setPhase("ended");
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

    setPhase("connecting");
    intentionalRef.current = false;
    reconnectAttempted.current = false;

    const { data } = await supabase.auth.getSession();
    const userId = data.session?.user?.id ?? null;

    if (!userId) {
      setPhase("idle");
      return;
    }

    setMyUserId(userId);

    let ticket: string;
    try {
      const result = await fetchWsTicket();
      ticket = result.ticket;
    } catch {
      setPhase("idle");
      return;
    }

    const wsBase = process.env.NEXT_PUBLIC_API_WS_URL ?? "ws://localhost:8000";
    const ws = new WebSocket(`${wsBase}/ws/battle?ticket=${encodeURIComponent(ticket)}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setPhase("idle");
      reconnectAttempted.current = false;
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
        setPhase("idle");
      }
    };

    ws.onerror = () => ws.close();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const joinQueue = useCallback((teamId: string) => {
    wsRef.current?.send(JSON.stringify({ type: "join_queue", team_id: teamId }));
  }, []);

  const leaveQueue = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: "leave_queue" }));
  }, []);

  const makeMove = useCallback((moveSlot: number) => {
    const bid = battleIdRef.current;
    if (!bid) return;
    wsRef.current?.send(JSON.stringify({ type: "make_move", battle_id: bid, move_slot: moveSlot }));
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
    wsRef.current?.close();
    setPhase("idle");
    setBattleState(null);
    setBattleId(null);
    battleIdRef.current = null;
    setLog([]);
    setEndInfo(null);
    setWaitingForOpponent(false);
    setOpponentDisconnected(false);
    setServerShuttingDown(false);
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
    connect,
    joinQueue,
    leaveQueue,
    makeMove,
    forfeit,
    disconnect,
  };
}
