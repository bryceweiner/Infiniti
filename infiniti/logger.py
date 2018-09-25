import logging,os,sys
from infiniti.params import *

logging.DEBUG_SEND = 11
logging.DEBUG_RECEIVE = 10
class LoggerWriter(object):
	def __init__(self, logger, level):
		# self.level is really like using log.debug(message)
		# at least in my case
		self.logger = logger
		self.level = level
		self.linebuf = ''

	def write(self, buf):
		for line in buf.rstrip().splitlines():
			self.logger.log(self.log_level, line.rstrip())

	def flush(self):
		# create a flush method so things can be flushed when
		# the system wants to. Not sure if simply 'printing'
		# sys.stderr is the correct way to do it, but it seemed
		# to work properly for me.
		self.logger.log(self.level,sys.stderr)

class LoggerClass(logging.getLoggerClass()):

	def send(self, msg, *args, **kwargs):
		if self.isEnabledFor(logging.DEBUG_SEND):
			self._log(logging.DEBUG_SEND, msg, args, **kwargs)

	def receive(self, msg, *args, **kwargs):
		if self.isEnabledFor(logging.DEBUG_RECEIVE):
			self._log(logging.DEBUG_RECEIVE, msg, args, **kwargs)

	def error(self, msg, *args, **kwargs):
		self._log(logging.ERROR, msg, args, **kwargs)

class LogFormatter(logging.Formatter):
	err_fmt     = '%(asctime)s ERROR: %(message)s'
	msg_rcv     = '%(asctime)s DEBUG: %(message)s'
	msg_snd     = '%(asctime)s SEND: %(message)s'
	default 	= '%(asctime)s - %(message)s'

	def __init__(self, fmt="%(levelno)s: %(msg)s"):
		logging.Formatter.__init__(self, self.default)

	def format(self, record):
		# Save the original format configured by the user
		# when the logger formatter was instantiated
		format_orig = self._fmt

		# Replace the original format with one customized by logging level
		if record.levelno == logging.DEBUG_RECEIVE:
			self._fmt = LogFormatter.msg_rcv
		elif record.levelno == logging.DEBUG_SEND:
			self._fmt = LogFormatter.msg_snd
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
logging.addLevelName(logging.DEBUG_SEND, "SEND")
logging.addLevelName(logging.DEBUG_RECEIVE, "RECEIVE")
logging.setLoggerClass(LoggerClass)
logger_handler.setFormatter(LogFormatter())
"""
stdout_logger = logging.getLogger('STDOUT')
sl = infiniti.logger.LoggerWriter(stdout_logger, logging.INFO)
sys.stdout = sl
stderr_logger = logging.getLogger('STDERR')
sl = infiniti.logger.LoggerWriter(stderr_logger, logging.ERROR)
sys.stderr = sl
"""

