"""Integration tests for the WebSocket battle endpoint."""
from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient

from app.main import create_app
from app.sockets.tickets import issue_ticket
from tests.conftest import TEST_USER_1, TEST_USER_2
from tests.helpers import make_pokemon


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_team():
    return [make_pokemon(name="Pikachu", hp=200, attack=100, defense=50, speed=90)]


async def _mock_fetch_team(team_id: str, user_id: str):
    return _make_team()


@pytest.fixture
def ws_app(monkeypatch):
    """App fixture with _fetch_team mocked to avoid Supabase calls."""
    monkeypatch.setattr("app.sockets.battle._fetch_team", _mock_fetch_team)
    return create_app()


@pytest.fixture
def ws_client(ws_app):
    with TestClient(ws_app) as client:
        yield client


# ─── Connection & auth ────────────────────────────────────────────────────────

class TestWebSocketAuth:
    def test_invalid_ticket_closes_with_4001(self, ws_client):
        with pytest.raises(Exception):
            with ws_client.websocket_connect("/ws/battle?ticket=bad-ticket") as ws:
                ws.receive_json()  # should not get here

    def test_valid_ticket_connects_successfully(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            # Connection accepted — send a harmless message to confirm the socket is alive
            ws.send_json({"type": "leave_queue"})
            msg = ws.receive_json()
            assert msg["type"] == "queue_left"

    def test_ticket_is_single_use(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            ws.send_json({"type": "leave_queue"})
            ws.receive_json()

        # Second connection with the same ticket should fail
        with pytest.raises(Exception):
            with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws2:
                ws2.receive_json()


# ─── Queue messages ───────────────────────────────────────────────────────────

class TestJoinQueue:
    def test_join_queue_without_team_id_returns_error(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            ws.send_json({"type": "join_queue"})
            msg = ws.receive_json()
        assert msg["type"] == "error"
        assert "team_id" in msg["message"]

    def test_join_queue_with_team_id_returns_queue_joined(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            ws.send_json({"type": "join_queue", "team_id": "team-abc"})
            msg = ws.receive_json()
        assert msg["type"] == "queue_joined"


class TestLeaveQueue:
    def test_leave_queue_returns_queue_left(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            ws.send_json({"type": "join_queue", "team_id": "team-abc"})
            ws.receive_json()  # queue_joined
            ws.send_json({"type": "leave_queue"})
            msg = ws.receive_json()
        assert msg["type"] == "queue_left"

    def test_leave_queue_when_not_queued_still_responds(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            ws.send_json({"type": "leave_queue"})
            msg = ws.receive_json()
        assert msg["type"] == "queue_left"


# ─── Unknown messages ─────────────────────────────────────────────────────────

class TestUnknownMessage:
    def test_unknown_type_returns_error(self, ws_client):
        ticket = issue_ticket(TEST_USER_1)
        with ws_client.websocket_connect(f"/ws/battle?ticket={ticket}") as ws:
            ws.send_json({"type": "nonsense_action"})
            msg = ws.receive_json()
        assert msg["type"] == "error"
        assert "nonsense_action" in msg["message"]


# ─── Two-player match flow ────────────────────────────────────────────────────

class TestMatchmakingFlow:
    def test_two_players_form_a_match(self, ws_app):
        ticket1 = issue_ticket(TEST_USER_1)
        ticket2 = issue_ticket(TEST_USER_2)

        with TestClient(ws_app) as client:
            with client.websocket_connect(f"/ws/battle?ticket={ticket1}") as ws1:
                with client.websocket_connect(f"/ws/battle?ticket={ticket2}") as ws2:
                    # P1 joins — one player isn't enough for a match
                    ws1.send_json({"type": "join_queue", "team_id": "team-1"})
                    assert ws1.receive_json()["type"] == "queue_joined"

                    # P2 joins — triggers match
                    ws2.send_json({"type": "join_queue", "team_id": "team-2"})

                    # P2 gets match_found then battle_start
                    msg = ws2.receive_json()
                    assert msg["type"] == "match_found"
                    assert msg["opponent_id"] == TEST_USER_1

                    msg = ws2.receive_json()
                    assert msg["type"] == "battle_start"
                    assert "state" in msg

                    # P1 also gets match_found then battle_start
                    msg = ws1.receive_json()
                    assert msg["type"] == "match_found"
                    assert msg["opponent_id"] == TEST_USER_2

                    msg = ws1.receive_json()
                    assert msg["type"] == "battle_start"
                    assert "state" in msg

    def test_battle_state_contains_both_players(self, ws_app):
        ticket1 = issue_ticket(TEST_USER_1)
        ticket2 = issue_ticket(TEST_USER_2)

        with TestClient(ws_app) as client:
            with client.websocket_connect(f"/ws/battle?ticket={ticket1}") as ws1:
                with client.websocket_connect(f"/ws/battle?ticket={ticket2}") as ws2:
                    ws1.send_json({"type": "join_queue", "team_id": "team-1"})
                    ws1.receive_json()  # queue_joined

                    ws2.send_json({"type": "join_queue", "team_id": "team-2"})
                    ws2.receive_json()  # match_found
                    battle_start = ws2.receive_json()

                    state = battle_start["state"]
                    player_ids = {state["player1"]["user_id"], state["player2"]["user_id"]}
                    assert TEST_USER_1 in player_ids
                    assert TEST_USER_2 in player_ids


# ─── Forfeit ─────────────────────────────────────────────────────────────────

class TestForfeit:
    def test_forfeit_ends_battle(self, ws_app):
        ticket1 = issue_ticket(TEST_USER_1)
        ticket2 = issue_ticket(TEST_USER_2)

        with TestClient(ws_app) as client:
            with client.websocket_connect(f"/ws/battle?ticket={ticket1}") as ws1:
                with client.websocket_connect(f"/ws/battle?ticket={ticket2}") as ws2:
                    # Start a match
                    ws1.send_json({"type": "join_queue", "team_id": "team-1"})
                    ws1.receive_json()  # queue_joined
                    ws2.send_json({"type": "join_queue", "team_id": "team-2"})

                    # Consume match_found + battle_start for both players
                    ws2.receive_json()  # match_found
                    battle_start = ws2.receive_json()  # battle_start
                    battle_id = battle_start["battle_id"]
                    ws1.receive_json()  # match_found
                    ws1.receive_json()  # battle_start

                    # P1 forfeits
                    ws1.send_json({"type": "forfeit", "battle_id": battle_id})

                    # Both should receive battle_end
                    end1 = ws1.receive_json()
                    assert end1["type"] == "battle_end"
                    assert end1["reason"] == "forfeit"
                    assert end1["winner_id"] == TEST_USER_2

                    end2 = ws2.receive_json()
                    assert end2["type"] == "battle_end"
                    assert end2["winner_id"] == TEST_USER_2


# ─── Make move ───────────────────────────────────────────────────────────────

class TestMakeMove:
    def test_move_received_broadcast_on_first_move(self, ws_app):
        ticket1 = issue_ticket(TEST_USER_1)
        ticket2 = issue_ticket(TEST_USER_2)

        with TestClient(ws_app) as client:
            with client.websocket_connect(f"/ws/battle?ticket={ticket1}") as ws1:
                with client.websocket_connect(f"/ws/battle?ticket={ticket2}") as ws2:
                    ws1.send_json({"type": "join_queue", "team_id": "team-1"})
                    ws1.receive_json()  # queue_joined
                    ws2.send_json({"type": "join_queue", "team_id": "team-2"})

                    ws2.receive_json()  # match_found
                    ws2.receive_json()  # battle_start
                    ws1.receive_json()  # match_found
                    battle_start = ws1.receive_json()  # battle_start
                    battle_id = battle_start["battle_id"]

                    # P1 submits a move
                    ws1.send_json({"type": "make_move", "battle_id": battle_id, "move_slot": 0})

                    # The room gets a move_received broadcast
                    msg = ws1.receive_json()
                    assert msg["type"] == "move_received"
                    assert msg["user_id"] == TEST_USER_1

    def test_both_moves_resolves_turn(self, ws_app):
        ticket1 = issue_ticket(TEST_USER_1)
        ticket2 = issue_ticket(TEST_USER_2)

        with TestClient(ws_app) as client:
            with client.websocket_connect(f"/ws/battle?ticket={ticket1}") as ws1:
                with client.websocket_connect(f"/ws/battle?ticket={ticket2}") as ws2:
                    ws1.send_json({"type": "join_queue", "team_id": "team-1"})
                    ws1.receive_json()
                    ws2.send_json({"type": "join_queue", "team_id": "team-2"})

                    ws2.receive_json()  # match_found
                    ws2.receive_json()  # battle_start
                    ws1.receive_json()  # match_found
                    battle_start = ws1.receive_json()  # battle_start
                    battle_id = battle_start["battle_id"]

                    ws1.send_json({"type": "make_move", "battle_id": battle_id, "move_slot": 0})
                    # move_received broadcast goes to both players
                    ws1.receive_json()  # move_received (from ws1's perspective)
                    ws2.receive_json()  # move_received (from ws2's perspective)

                    ws2.send_json({"type": "make_move", "battle_id": battle_id, "move_slot": 0})

                    # Both players receive turn_result
                    turn1 = ws1.receive_json()
                    turn2 = ws2.receive_json()
                    assert turn1["type"] == "turn_result"
                    assert turn2["type"] == "turn_result"
                    assert "state" in turn1
                    assert "log" in turn1
