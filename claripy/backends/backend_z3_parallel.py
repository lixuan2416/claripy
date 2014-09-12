import os
import pickle
import threading

from .backend_z3 import BackendZ3

class BackendZ3Parallel(BackendZ3):
	def __init__(self, clrp):
		BackendZ3.__init__(self, clrp)
		self._child = False
		self._lock = threading.RLock()

	def _background(self, f, *args, **kwargs):
		f = getattr(BackendZ3, f)
		if self._child:
			return f(self, *args, **kwargs)

		p_r, p_w = os.pipe()
		p = os.fork()
		if p == 0:
			try:
				r = f(self, *args, **kwargs)
			except UnsatError as e:
				r = e

			#print "WRITING (%d)" % os.getpid()
			pickled = pickle.dumps(r)
			written = 0
			while written < len(pickled):
				written += os.write(p_w, pickled[written:])
			os.close(p_w)
			os.close(p_r)
			#print "WROTE (%d)" % os.getpid()
			os.kill(os.getpid(), 9)
			#os.abort()
			#sys.exit(1)
		else:
			os.close(p_w)
			#print "READING (from %d)" % p
			try:
				strs = [ os.read(p_r, 1024*1024) ]
				while strs[-1] != "": strs.append(os.read(p_r, 1024*1024))
			except EOFError:
				raise Exception("WTF")
			os.close(p_r)
			#print "READ (from %d)" % p

			#thread.start_new_thread(os.wait, ())
			r = pickle.loads("".join(strs))
			if isinstance(r, Exception): raise r
			else: return r

	def _synchronize(self, f, *args, **kwargs):
		self._lock.acquire()
		try:
			return getattr(BackendZ3, f)(self, *args, **kwargs)
		finally:
			self._lock.release()

	# backgrounded
	def results(self, *args, **kwargs):
		return self._background('results', *args, **kwargs)
	def eval(self, *args, **kwargs):
		return self._background('eval', *args, **kwargs)
	def min(self, *args, **kwargs):
		return self._background('min', *args, **kwargs)
	def max(self, *args, **kwargs):
		return self._background('max', *args, **kwargs)

	def convert(self, *args, **kwargs):
		return self._synchronize('convert', *args, **kwargs)
	def abstract(self, *args, **kwargs):
		return self._synchronize('abstract', *args, **kwargs)
	def size(self, *args, **kwargs):
		return self._synchronize('size', *args, **kwargs)
	def solver(self, *args, **kwargs):
		return self._synchronize('solver', *args, **kwargs)
	def add(self, *args, **kwargs):
		return self._synchronize('add', *args, **kwargs)
	def check(self, *args, **kwargs):
		return self._synchronize('check', *args, **kwargs)
	def simplify(self, *args, **kwargs):
		return self._synchronize('simplify', *args, **kwargs)
	def call(self, *args, **kwargs):
		return self._synchronize('call', *args, **kwargs)
	def simplify_expr(self, *args, **kwargs):
		return self._synchronize('simplify_expr', *args, **kwargs)

from ..result import UnsatError
