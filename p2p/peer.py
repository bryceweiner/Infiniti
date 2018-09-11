import socket, time

from p2p.protocol.exceptions import NodeDisconnectException
from p2p.protocol.buffer import ProtocolBuffer
from p2p.protocol.serializers import *
from utils.db import open_db,writebatch
from infiniti.params import *
import infiniti.rpc as infiniti_rpc
from infiniti.factories import process_mempool, process_block

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

peer_db_path = os.path.join(DATA_PATH,"peers")

class InfinitiPeer(object):
	"""
	The base class for a Tao network client.  This class
	will handle the initial handshake and responding to pings,
	and socket connections.
	"""

	coin = "tao"
	db = None   
	socket = None
	mempool_manager = None
	counter = 0
	running = 0

	def __init__(self, logger, peerip, port, my_ip_address, my_port):
		self.logger = logger
		self.buffer = ProtocolBuffer()
		self.peerip = peerip
		self.port = port if port is not None else param_query(NETWORK,'p2p_port')
		self.is_connected = False
		self.error = False
		self.exit = False
		self.socket = None
		self.remote_height = 0
		self.my_ip_address = my_ip_address
		self.my_port = my_port

	def touch_peer(self):
		db = open_db(peer_db_path,self.logger)
		db.put(self.peerip+":"+str(self.port),str(int(time.time())))
	def error_peer(self,errno):
		db = open_db(peer_db_path,self.logger)
		db.put(self.peerip+":"+str(self.port),str(errno))				

	def message_received(self, message_header, message):
		"""
		This method will be called for every message, and then will
		delegate to the appropriate handle_* function for the given
		message (if it exists).

		Args:
			message_header: The message header
			message: The message object
		"""
		self.logger.receive("{0} - {1} - {2}".format(self.peerip, message_header.command, str(message)))
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
		self.logger.send("{0} - {1}".format(self.peerip, str(message)))
		try:
			self.socket.sendall(message.get_message(self.coin))
		except socket.error as err:
			self.error_peer(err.errno)
			self.logger.error("IP: {0} : Send Message Socket Error({1}): {2}".format(self.peerip,err.errno, err.strerror))
			self.error = True

	def send_ping(self): 
		p = Ping()
		self.send_message(p)

	def get_peers(self):
		ga = GetAddr()
		self.send_message(ga)

	def connected(self):
		# Get list of peers
		self.is_connected = True
		self.touch_peer()
		self.logger.info("{0} - Connected.".format(self.peerip))
		gp = GetAddr()
		self.send_message(gp)
		mp = MemPool()
		self.send_message(mp)

	def handle_inv(self, message_header, message):
		self.logger.receive("Received new inventory data from {0}".format(self.peerip))  
		gd = GetData()
		gd.inventory = message.inventory
		self.send_message(gd)

	def handle_tx(self, message_header, message):
		self.logger.receive("Received new mempool transaction from {0}".format(self.peerip))
		self.logger.receive("{0}".format(message))
		process_mempool(message)

	def handle_block(self, message_header, message):
		self.logger.receive("Received new block {0} from {1}".format(message.calculate_hash(), self.peerip))
		process_block(message)

	def handle_pong(self,messaage_header, message):
		gp = SmsgPing()
		# Only send SMsgPong if the client can relay secure messages
		self.send_message(gp)

	def handle_addr(self, message_header, message):
		"""
		This method will handle incoming inventories of network 
		peers.
		Args:
			message_header: The message header
			message: The list of peers
		"""
		db = open_db(peer_db_path,self.logger)
		wb = writebatch()
		self.logger.info("Unpacking new peers from {0}".format(self.peerip))
		try:
			for peer in message.addresses:
				_p = db.get("{0}:{1}".format(peer.ip_address,str(peer.port)))
				if _p is None:
					wb.put("{0}:{1}".format(peer.ip_address,str(peer.port)),str(int(time.time())))
				try:
					infiniti_rpc._CONNECTION.addnode("{0}:{1}".format(peer.ip_address,str(peer.port)),'add')
				except:
					pass
			db.write(wb)
		except Exception as e:
			self.error = True
			self.logger.error(e)

	def open(self):
		# connect
		try:
			self.logger.info("Connecting to {0}:{1}".format(self.peerip,str(self.port)))
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.settimeout(60)
			self.socket.connect((self.peerip, self.port))
		except socket.error as err:
			self.error_peer(err.errno)
			if self.is_connected:
				self.logger.error("IP: {0} : Was Open Socket Error({1}): {2}".format(self.peerip,err.errno, err.strerror))
			else:
				self.logger.error("IP: {0} : Connection refused.".format(self.peerip))
			self.error = True
			self.is_connected = False 
			return
		# send our version
		self.socket.settimeout(None)
		self.is_connected = True
		v = Version(self.peerip, self.port, self.my_ip_address,self.my_port)
		self.send_message(v)

	def close(self):
		if self.socket is not None:
			self.socket.close()
		self.exit = True
		self.is_connected = False 
		self.logger.status_message("{0} - Connection closed.".format(self.peerip))

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

	def loop(self):
		"""
		This is the main method of the client, it will enter
		in a receive/send loop.
		"""
