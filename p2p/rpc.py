# Originally from https://gist.github.com/dergachev/7028596

# taken from http://www.piware.de/2011/01/creating-an-https-server-in-python/
# generate server.xml with the following command:
#    openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
# run as follows:
#    python simple-https-server.py
# then in your browser, visit:
#    https://localhost:4443
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from p2p import version
import BaseHTTPServer, SimpleHTTPServer
import ssl
import p2p.logger as logger
import sys, os, re, shutil, json, urllib, urllib2, BaseHTTPServer
from params import *

# Fix issues with decoding HTTP responses
reload(sys)
sys.setdefaultencoding('utf8')

here = os.path.dirname(os.path.realpath(__file__))

def getinfo(handler):
	obj =	{
		    "version" : "node " + version,
		    "protocolversion" : param_query(NETWORK,'protocol_version'),
		    "walletversion" : 60000,
		    "balance" : 75780.09350130,
		    "darksend_balance" : 0.00000000,
		    "newmint" : 0.00000000,
		    "stake" : 0.00000000,
		    "blocks" : 133226,
		    "timeoffset" : 0,
		    "moneysupply" : 33144711.43683799,
		    "connections" : 8,
		    "proxy" : "",
		    "ip" : "98.182.22.167",
		    "difficulty" : 5613046.88822863,
		    "testnet" : False,
		    "keypoololdest" : 1472184481,
		    "keypoolsize" : 1001,
		    "paytxfee" : 0.00000000,
		    "mininput" : 0.00000000,
		    "unlocked_until" : 0,
		    "errors" : ""
		}
	return json.dumps(obj)

def rest_call_json(url, payload=None, with_payload_method='PUT'):
	"""
	REST call with JSON decoding of the response and JSON payloads
	"""
	if payload:
		if not isinstance(payload, basestring):
			payload = json.dumps(payload)
		# PUT or POST
		response = urllib2.urlopen(MethodRequest(url, payload, {'Content-Type': 'application/json'}, method=with_payload_method))
	else:
		# GET
		response = urllib2.urlopen(url)
	response = response.read().decode()
	return json.loads(response)

class MethodRequest(urllib2.Request):
	"""
	See: https://gist.github.com/logic/2715756
	"""
	def __init__(self, *args, **kwargs):
		if 'method' in kwargs:
			self._method = kwargs['method']
			del kwargs['method']
		else:
			self._method = None
		return urllib2.Request.__init__(self, *args, **kwargs)

	def get_method(self, *args, **kwargs):
		return self._method if self._method is not None else urllib2.Request.get_method(self, *args, **kwargs)

class RESTRequestHandler(BaseHTTPRequestHandler):
	def __init__(self, *args, **kwargs):
		self.routes = {
			r'^/$': {'file': 'web/index.html', 'media_type': 'text/html'},
			r'^/getinfo$': {'GET': getinfo, 'media_type': 'application/json'},}
			#r'^/record/': {'GET': get_record, 'PUT': set_record, 'DELETE': delete_record, 'media_type': 'application/json'}}
		
		return BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
	
	def log_message(self, format, *args):
		pass
		
	def do_HEAD(self):
		self.handle_method('HEAD')
	
	def do_GET(self):
		self.handle_method('GET')

	def do_POST(self):
		self.handle_method('POST')

	def do_PUT(self):
		self.handle_method('PUT')

	def do_DELETE(self):
		self.handle_method('DELETE')
	
	def get_payload(self):
		payload_len = int(self.headers.getheader('content-length', 0))
		payload = self.rfile.read(payload_len)
		payload = json.loads(payload)
		return payload
		
	def handle_method(self, method):
		route = self.get_route()
		if route is None:
			self.send_response(404)
			self.end_headers()
			self.wfile.write('Route not found\n')
		else:
			if method == 'HEAD':
				self.send_response(200)
				if 'media_type' in route:
					self.send_header('Content-type', route['media_type'])
				self.end_headers()
			else:
				if 'file' in route:
					if method == 'GET':
						try:
							f = open(os.path.join(here, route['file']))
							try:
								self.send_response(200)
								if 'media_type' in route:
									self.send_header('Content-type', route['media_type'])
								self.end_headers()
								shutil.copyfileobj(f, self.wfile)
							finally:
								f.close()
						except:
							self.send_response(404)
							self.end_headers()
							self.wfile.write('File not found\n')
					else:
						self.send_response(405)
						self.end_headers()
						self.wfile.write('Only GET is supported\n')
				else:
					if method in route:
						content = route[method](self)
						if content is not None:
							self.send_response(200)
							if 'media_type' in route:
								self.send_header('Content-type', route['media_type'])
							self.end_headers()
							if method != 'DELETE':
								self.wfile.write(json.dumps(content))
						else:
							self.send_response(404)
							self.end_headers()
							self.wfile.write('Not found\n')
					else:
						self.send_response(405)
						self.end_headers()
						self.wfile.write(method + ' is not supported\n')
					
	
	def get_route(self):
		for path, route in self.routes.iteritems():
			if re.match(path, self.path):
				return route
		return None

class RPCServerThread(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class RPCServer(object):
	def start(self,ip='localhost',port=8000):
		self.rpc_ip = ip
		self.rpc_port = port
		self.httpd = RPCServerThread((self.rpc_ip, self.rpc_port), RESTRequestHandler)
		logger.status_message("RPC server started.")
		self.httpd.serve_forever()