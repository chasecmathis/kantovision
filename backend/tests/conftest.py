# Set fake env vars BEFORE any app imports so lru_cache captures them.
import os

os.environ.setdefault("SUPABASE_URL", "https://test.example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

from unittest.mock import MagicMock  # noqa: E402

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

import app.battle.manager as battle_manager  # noqa: E402
import app.battle.matchmaking as matchmaking  # noqa: E402
import app.sockets.tickets as tickets_mod  # noqa: E402
from app.dependencies import get_current_user_id  # noqa: E402
from app.main import create_app  # noqa: E402
from app.sockets import battle as battle_socket  # noqa: E402
from app.sockets.connections import manager as ws_manager  # noqa: E402

TEST_USER_1 = "user-aaaa-1111-1111-111111111111"
TEST_USER_2 = "user-bbbb-2222-2222-222222222222"


def make_mock_user(user_id: str) -> MagicMock:
    m = MagicMock()
    m.id = user_id
    return m


@pytest.fixture(autouse=True)
def reset_global_state():
    """Wipe all in-memory singletons before every test."""
    yield
    battle_manager._reset_for_testing()
    matchmaking._reset_for_testing()
    tickets_mod._reset_for_testing()
    ws_manager._rooms.clear()
    ws_manager._sockets.clear()
    for task in list(battle_socket._pending_forfeits.values()):
        task.cancel()
    battle_socket._pending_forfeits.clear()
    for task in list(battle_socket._move_timeouts.values()):
        task.cancel()
    battle_socket._move_timeouts.clear()
    battle_socket._rate_windows.clear()
    battle_socket._recent_battle_ends.clear()
    battle_socket._turn_started_at.clear()


@pytest.fixture
def app_instance():
    _app = create_app()
    _app.dependency_overrides[get_current_user_id] = lambda: make_mock_user(TEST_USER_1)
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app_instance):
    with TestClient(app_instance) as c:
        yield c
