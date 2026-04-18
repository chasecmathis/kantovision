import json
import logging
import sys


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
