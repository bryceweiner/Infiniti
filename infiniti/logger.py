import logging,os
from infiniti.params import *

logging.DEBUG_SEND = 9 
logging.DEBUG_RECEIVE = 10

def debug_recv(self, message, *args, **kws):
	# Yes, logger takes its '*args' as 'args'.
	if self.isEnabledFor(logging.DEBUG_RECEIVE):
		self._log(logging.DEBUG_RECEIVE, message, args, **kws) 

def debug_send(self, message, *args, **kws):
	# Yes, logger takes its '*args' as 'args'.
	if self.isEnabledFor(logging.DEBUG_SEND_NUM):
		self._log(logging.DEBUG_SEND, message, args, **kws) 

class LogFormatter(logging.Formatter):
	err_fmt     = ':%(asctime)s - ERROR - %(message)s'
	msg_rcv     = 'P2P:%(asctime)s - Recv Message - %(message)s'
	msg_snd     = 'P2P:%(asctime)s - Send Message - %(message)s'
	default = '%(asctime)s - %(message)s'

	def __init__(self, fmt="%(levelno)s: %(msg)s"):
		logging.addLevelName(logging.DEBUG_SEND, "SEND")
		logging.Logger.send = debug_send
		logging.addLevelName(logging.DEBUG_RECEIVE, "RECV")
		logging.Logger.receive = debug_recv
		logging.Formatter.__init__(self, fmt)

	def format(self, record):
		# Save the original format configured by the user
		# when the logger formatter was instantiated
		format_orig = self._fmt

		# Replace the original format with one customized by logging level
		if record.levelno == logging.DEBUG_SEND:
			self._fmt = LogFormatter.msg_snd
		if record.levelno == logging.DEBUG_RECEIVE:
			self._fmt = LogFormatter.msg_rcv
		if record.levelno == logging.DEBUG:
			self._fmt = LogFormatter.default
		elif record.levelno == logging.INFO:
			self._fmt = LogFormatter.default
		elif record.levelno == logging.ERROR:
			self._fmt = LogFormatter.err_fmt

		# Call the original formatter class to do the grunt work
		result = logging.Formatter.format(self, record)

		# Restore the original format configured by the user
		self._fmt = format_orig

		return result

logger_handler = logging.FileHandler(os.path.join(ROOT_PATH, 'infiniti.log'))  # Handler for the logger
logger_handler.setFormatter(LogFormatter())

