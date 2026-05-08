# ─── Inbound message types (client → server) ─────────────────────────────────

MSG_JOIN_QUEUE = "join_queue"
MSG_LEAVE_QUEUE = "leave_queue"
MSG_MAKE_ACTION = "make_action"
MSG_FORFEIT = "forfeit"
MSG_SELECT_LEAD = "select_lead"
MSG_SUBMIT_SWITCH = "submit_switch"

# ─── Outbound message types (server → client) ────────────────────────────────

MSG_QUEUE_JOINED = "queue_joined"
MSG_QUEUE_LEFT = "queue_left"
MSG_MATCH_FOUND = "match_found"
MSG_TEAM_PREVIEW = "team_preview"
MSG_BATTLE_START = "battle_start"
MSG_BATTLE_RESUMED = "battle_resumed"
MSG_BATTLE_END = "battle_end"
MSG_TURN_RESULT = "turn_result"
MSG_MOVE_RECEIVED = "move_received"
MSG_FORCED_SWITCH = "forced_switch"
MSG_OPPONENT_DISCONNECTED = "opponent_disconnected"
MSG_OPPONENT_RECONNECTED = "opponent_reconnected"
MSG_SERVER_SHUTDOWN = "server_shutdown"
MSG_ERROR = "error"
