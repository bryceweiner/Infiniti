import socket, time

from p2p.protocol.exceptions import NodeDisconnectException
from p2p.protocol.buffer import ProtocolBuffer
from p2p.protocol.serializers import *
from utils.db import open_db
from infiniti.params import *

def intToBytes(n):
	b = bytearray([0, 0, 0, 0])   # init
	b[3] = n & 0xFF
	n >>= 8
	b[2] = n & 0xFF
	n >>= 8
	b[1] = n & 0xFF
	n >>= 8
	b[0] = n & 0xFF    
	
	# Return the result or as bytearray or as bytes (commented out)
	##return bytes(b)  # uncomment if you need
	return b
	
class InfinitiPeer(object):
	"""
	The base class for a Tao network client.  This class
	will handle the initial handshake and responding to pings.
	"""

	coin = "tao"

	def __init__(self, logger, peerip, port=None):
		self.logger = logger
		self.buffer = ProtocolBuffer()
		self.peerip = peerip
		self.port = port if port is not None else param_query(NETWORK,'p2p_port')
		self.is_connected = False
		self.error = False
		self.exit = False
		self.socket = None
		self.remote_height = 0


	def open(self,ip_address,port):
		# connect
		self.ip_address = ip_address
		self.network_port = port
		try:
			if self.socket is None:
				self.logger.status_message("Connecting to " + self.peerip + ":" + str(self.port))
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.connect((self.peerip, self.port))
			else:
				peer = socket.getpeername()
				self.peerip = peer[0]
				self.port = peer[1]
				self.logger.status_message("Connection from " + self.peerip + ":" + str(self.port))
		except socket.error as err:
			#self.db.update_peer(self,err.errno)
			self.logger.error_message("IP: {0} : Socket Error({1}): {2}".format(self.peerip,err.errno, err.strerror))
			self.error = True
			return
		# send our version
		v = Version(self.peerip, self.port, self.ip_address,self.network_port)
		self.send_message(v)

	def close(self):
		if self.socket is not None:
			self.socket.close()
		self.exit = True
		self.is_connected = False 

	def handle_version(self, message_header, message):
		"""
		This method will handle the Version message and
		will send a VerAck message when it receives the
		Version message.

		Args:
			message_header: The Version message header
			message: The Version message
		"""
		self.remote_height = message.start_height
		self.send_message(VerAck())
		self.connected()

	def connected(self):
		"""
		Called once we've exchanged version information and can make
		calls on the network.
		"""
		pass

	def handle_ping(self, message_header, message):
		"""
		This method will handle the Ping message and then
		will answer every Ping message with a Pong message
		using the nonce received.

		Args:
			message_header: The header of the Ping message
			message: The Ping message
		"""
		pong = Pong()
		pong.nonce = message.nonce
		self.send_message(pong)

	def message_received(self, message_header, message):
		"""
		This method will be called for every message, and then will
		delegate to the appropriate handle_* function for the given
		message (if it exists).

		Args:
			message_header: The message header
			message: The message object
		"""
		handle_func_name = "handle_" + message_header.command
		handle_func = getattr(self, handle_func_name, None)
		if handle_func:
			handle_func(message_header, message)

	def send_message(self, message):
		"""
		This method will serialize the message using the
		appropriate serializer based on the message command
		and then it will send it to the socket stream.

		:param message: The message object to send
		"""
		try:
			self.socket.sendall(message.get_message(self.coin))
		except socket.error as err:
			#self.db.update_peer(self,err.errno)
			self.logger.error_message("IP: {0} : Socket Error({1}): {2}".format(self.peerip,err.errno, err.strerror))
			self.error = True

	def loop(self):
		"""
		This is the main method of the client, it will enter
		in a receive/send loop.
		"""
		while not self.error and not self.exit:
			try:
				data = self.socket.recv(1024 * 8)

				if len(data) <= 0:
					self.is_connected = False
					break

				self.buffer.write(data)
				message_header, message = self.buffer.receive_message()
				if message is not None:
					self.message_received(message_header, message)
			except socket.error as err:
				self.error = True
				self.is_connected = False 
				#self.db.update_peer(self,err.errno)
				self.logger.error_message("IP: {0} : Socket Error({1}): {2}".format(self.peerip,err.errno, err.strerror))				
		self.logger.status_message("{0} - Node disconnected.".format(self.peerip))
		self.close()