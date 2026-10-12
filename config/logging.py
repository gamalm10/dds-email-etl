import logging
import sys

from services.auto_fetch_status import install_log_handler


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setLevel(logging.INFO)
    logging.getLogger("services.imap_listener").setLevel(logging.DEBUG)
    install_log_handler()
