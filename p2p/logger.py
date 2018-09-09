import logging


log = logging.getLogger('p2p')
logger_handler = logging.FileHandler("p2p.log")  # Handler for the logger
log.setLevel(logging.DEBUG)
log.addHandler(logger_handler)

default_formatter = logging.Formatter(
    '%(asctime)s - %(message)s')
error_formatter = logging.Formatter(
    '%(asctime)s - ERROR - %(message)s')
msgrecv_formatter = logging.Formatter(
    '%(asctime)s - Recv Message - %(message)s')
msgsend_formatter = logging.Formatter(
    '%(asctime)s - Send Message - %(message)s')

def error_message(msg):
    logger_handler.setFormatter(default_formatter)        
    log.error("%s", msg)

def status_message(msg):
    logger_handler.setFormatter(default_formatter)        
    log.info("%s", msg)

def recv_message(msg):
    logger_handler.setFormatter(msgrecv_formatter)        
    log.debug("%s", msg)

def send_message(msg):
    logger_handler.setFormatter(msgsend_formatter)        
    log.debug("%s", msg)

