import logging
from singleton_decorator import singleton

@singleton
class Logger:
    def __init__(self):
        """Initialize the singleton logger instance."""
        self._logger = logging.getLogger("GlobalLogger")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False  # Prevent duplicate log entries from root

        # Define log format
        FORMAT = logging.Formatter(
            fmt="%(asctime)s - %(levelname).3s - %(filename)s:%(lineno).3d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(FORMAT)

        # console_handler.addFilter(log_filter)
        self._logger.addHandler(console_handler)

        # Suppress verbose logs globally
        logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        logging.getLogger("flask.cli").setLevel(logging.ERROR)
        logging.getLogger("google_genai.models").setLevel(logging.ERROR)
        logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

    def get_logger(self):
        """Return the logger instance."""
        return self._logger

# Create a global logger instance
logger = Logger().get_logger()