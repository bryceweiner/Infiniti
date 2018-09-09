from node.protocol.serializers import *
import Queue
class MemPoolManager(Queue.Queue):
	_getblocks = True
	def getblocks_ok(self):
		self._getblocks=True
	def getblocks_not_ok(self):
		self._getblocks=False
	def can_getblocks(self):
		return self._getblocks
	def items(self):
		return list(self.queue)

	def add(self, item):
		if item not in self.items():
			self.put(item)

	def remove(self, item):
		copy = []
		while True:
			try:
				elem = self.get(block=False)
			except Empty:
				break
			else:
				copy.append(elem)
		for elem in copy:
			if elem != item:
				q.put(elem)

	def size(self):
		return len(self.queue)

	def empty(self):
		self.mempool = []
		self.mutex.acquire()
		self.queue.clear()
		self.all_tasks_done.notify_all()
		self.unfinished_tasks = 0
		self.mutex.release()
