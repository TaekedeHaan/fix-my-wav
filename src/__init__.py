import logging
import pathlib
from datetime import date

LOG_DIRECOTRY = "logs"
LOG_FILE = f"{date.today()}.log"

log_file = pathlib.Path(LOG_DIRECOTRY) / LOG_FILE
log_file.resolve().parent.mkdir(parents=True, exist_ok=True)

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
handler_console = logging.StreamHandler()
handler_file = logging.FileHandler(log_file)

handler_console.setLevel(logging.DEBUG)
handler_file.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
format = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
handler_console.setFormatter(format)
handler_file.setFormatter(format)


# Add handlers to the logger
logger.setLevel(logging.DEBUG)
logger.addHandler(handler_console)
logger.addHandler(handler_file)
