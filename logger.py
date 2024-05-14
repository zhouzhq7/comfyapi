import os
import logging
import datetime

# Get the current time and format it as a string
timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

# Create the logger
logger = logging.getLogger('comfy_logger')
logger.setLevel(logging.DEBUG)

# Create console handler and set the logging level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

os.makedirs('./logs', exist_ok=True)

# Create file handler and set the logging level
log_filename = f'./logs/comfy_{timestamp}.log'
fh = logging.FileHandler(log_filename)
fh.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(ch)
logger.addHandler(fh)