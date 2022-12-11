"""Submodule containing the CLI command handlers."""

import logging
import sys

from iceflix.main import MainApp
from iceflix.client import Client


LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'


def setup_logging():
    """Configure the logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
    )


def client():
    """Handles the IceFlix client CLI command."""
    setup_logging()
    logging.info("Starting IceFlix client...")
    sys.exit(Client().main(sys.argv))
    
