import logging
logger = logging.getLogger("AnalystGPT")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)