#!/usr/bin/python

from __future__ import print_function
import functools
import time
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor
import tornado
import tornado.ioloop
import tornado.web
import libsplooshkaboom

libsplooshkaboom.initialize()

executor = ThreadPoolExecutor(32)

def square_to_num(xy):
	return xy[0] + 8 * xy[1]

def num_to_square(num):
	return num % 8, num / 8

cache = {}

def compute_sploosh_kaboom(hits, misses, squids_gotten):
	global cache

	# Make sure all of our values are sane.
	assert isinstance(hits, list)
	assert isinstance(misses, list)
	assert isinstance(squids_gotten, int)
	assert all(isinstance(elem, int) and 0 <= elem < 64 for elem in (hits + misses))
	assert len(hits) <= 64 and len(misses) <= 64

	if len(cache) > 10000:
		print("Emptying cache.")
		cache = {}

	key = (
		tuple(hits),
		tuple(misses),
		squids_gotten,
	)
	if key not in cache:
		results = libsplooshkaboom.Results()
		hits = libsplooshkaboom.vectori(hits)
		misses = libsplooshkaboom.vectori(misses)
		is_possible = libsplooshkaboom.do_computation(
			results,
			hits,
			misses,
			squids_gotten,
		)
		if not is_possible:
			cache[key] = False, 0
		else:
			cache[key] = zip(*[iter(list(results.probabilities))]*8), results.observation_prob
	return cache[key]

possible_moves = [num_to_square(i) for i in range(64)]

def do_work(payload):
	print("Working on:", payload)
	hit_squares  = [square_to_num(square) for square in payload["hits"]]
	miss_squares = [square_to_num(square) for square in payload["misses"]]
	distribution, observation_prob = compute_sploosh_kaboom(
		hit_squares,
		miss_squares,
		payload["squids_gotten"],
	)
	if distribution is False:
		return {
			"is_possible": False,
		}
	all_tested = set(num_to_square(n) for n in (hit_squares + miss_squares))
	best_square = None
	best_score = -1
	for square in possible_moves:
		if square in all_tested:
			continue
		score = distribution[square[1]][square[0]]
		if score > best_score:
			best_score = score
			best_square = square
	return {
		"is_possible": True,
		"probabilities": distribution,
		"highest_prob": best_square,
		"observation_prob": observation_prob,
	}

class APIHandler(tornado.web.RequestHandler):
	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

	@tornado.gen.coroutine
	def post(self):
		start = time.time()
		print(repr(self.request))
		payload = json.loads(self.request.body)
		result = yield executor.submit(do_work, payload)
		print("Response time:", time.time() - start)
		self.write(result)

def make_app():
	return tornado.web.Application([
		(r"/sk", APIHandler),
	])

if __name__ == "__main__":
	app = make_app()
	app.listen(1234)
	tornado.ioloop.IOLoop.current().start()

