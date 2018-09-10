#!/usr/bin/env python
import sys, os, time, atexit
import signal, lockfile
import infiniti.logger as _logger
import logging
from infiniti.params import *
from functools import partial

from service import find_syslog, Service

class Daemon(Service):
	"""
		A generic daemon class.

		Usage: subclass the Daemon class and override the run() method
	"""
	def __init__(self, *args, **kwargs):
		super(Daemon, self).__init__(*args, **kwargs)
		self.logger.addHandler(_logger.logger_handler)
		self.logger.setLevel(logging.DEBUG_RECEIVE)

	def restart(self):
		"""
		Restart the daemon
		"""
		print "Infiniti Restarting..."
		self.stop()
		self.start()
