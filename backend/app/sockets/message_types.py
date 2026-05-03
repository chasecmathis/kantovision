# ─── Inbound message types (client → server) ─────────────────────────────────

MSG_JOIN_QUEUE = "join_queue"
MSG_LEAVE_QUEUE = "leave_queue"
MSG_MAKE_MOVE = "make_move"
MSG_FORFEIT = "forfeit"

# ─── Outbound message types (server → client) ────────────────────────────────

MSG_QUEUE_JOINED = "queue_joined"
MSG_QUEUE_LEFT = "queue_left"
MSG_MATCH_FOUND = "match_found"
MSG_BATTLE_START = "battle_start"
MSG_BATTLE_RESUMED = "battle_resumed"
MSG_BATTLE_END = "battle_end"
MSG_TURN_RESULT = "turn_result"
MSG_MOVE_RECEIVED = "move_received"
MSG_OPPONENT_DISCONNECTED = "opponent_disconnected"
MSG_OPPONENT_RECONNECTED = "opponent_reconnected"
MSG_SERVER_SHUTDOWN = "server_shutdown"
MSG_ERROR = "error"
