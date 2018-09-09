import logging,os
from infiniti.params import *


log = logging.getLogger('infiniti')

logger_handler = logging.FileHandler(os.path.join(ROOT_PATH, 'infiniti.log'))  # Handler for the logger
log.setLevel(logging.DEBUG)
log.addHandler(logger_handler)

def error_message(msg,name='Infiniti'):
    error_formatter = logging.Formatter(
        name + ':%(asctime)s - ERROR - %(message)s')
    logger_handler.setFormatter(default_formatter)        
    log.error("%s", msg)

def status_message(msg,name='Infiniti'):
    default_formatter = logging.Formatter(
        name + ':%(asctime)s - %(message)s')
    logger_handler.setFormatter(default_formatter)        
    log.info("%s", msg)

def recv_message(msg):
    msgrecv_formatter = logging.Formatter(
        'P2P:%(asctime)s - Recv Message - %(message)s')
    logger_handler.setFormatter(msgrecv_formatter)        
    log.debug("%s", msg)

def send_message(msg):
    msgsend_formatter = logging.Formatter(
        'P2P:%(asctime)s - Send Message - %(message)s')
    logger_handler.setFormatter(msgsend_formatter)        
    log.debug("%s", msg)

