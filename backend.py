#!/usr/bin/python

import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor
import tornado
import tornado.ioloop
import tornado.web
import libsplooshkaboom

libsplooshkaboom.initialize()

executor = ThreadPoolExecutor(32)

def compute_sploosh_kaboom(hits, misses, squids_gotten):
	# Make sure all of our values are sane.
	assert isinstance(hits, list)
	assert isinstance(misses, list)
	assert isinstance(squids_gotten, int)
	assert all(isinstance(elem, int) and 0 <= elem < 64 for elem in (hits + misses))
	assert len(hits) <= 64 and len(misses) <= 64

	results = libsplooshkaboom.Results()
	hits = libsplooshkaboom.vectori(hits)
	misses = libsplooshkaboom.vectori(misses)
	libsplooshkaboom.do_computation(
		results,
		hits,
		misses,
		squids_gotten,
	)
	return zip(*[iter(list(results.probabilities))]*8)

def do_work(payload):
	distribution = compute_sploosh_kaboom(payload["hits"], payload["misses"], payload["squids_gotten"])
	return {
		"proabilities": distribution,
		"highest_prob": [int(i) for i in np.argmax(distribution)],
	}

class APIHandler(tornado.web.RequestHandler):
	@tornado.gen.coroutine
	def post(self):
		payload = json.loads(self.request.body)
		result = yield executor.submit(do_work, payload)
		self.write(result)

def make_app():
	return tornado.web.Application([
		(r"/sk", APIHandler),
	])

if __name__ == "__main__":
	app = make_app()
	app.listen(1234)
	tornado.ioloop.IOLoop.current().start()

