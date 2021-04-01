#!/usr/bin/python

from __future__ import print_function
import functools
import time
import json
import tornado
import tornado.ioloop
import tornado.web
import sqlite3

tornado.log.enable_pretty_logging()

class BigBrotherDB:
    def __init__(self):
        self.conn = sqlite3.connect("sk_bigbrother.db")
        for s in [
            """
                create table if not exists users (
                    username text primary key,
                    token text
                )
            """,
            """
                create table if not exists events (
                    combined_event_key text primary key,
                    event_key integer,
                    session text,
                    username text,
                    event_data text,
                    logging_context text,
                    timestamp real
                )
            """,
        ]:
            self.conn.execute(s)

    def credential_check(self, username, token):
        for row in self.conn.execute("select token from users where username = ?", (username,)):
            return row[0] == token

    def create_user(self, username, token):
        self.conn.execute("insert or replace into users values (?, ?)", (username, token))

    def get_events(self, username):
        for row in self.conn.execute(
            "select event_key, session, event_data from events where username = ?",
            (username,),
        ):
            yield {
                "event_key": row[0],
                "session": row[1],
                "event_data": json.loads(row[2]),
            }

    def insert_row(self, record, logging_context):
        assert isinstance(record["event_key"], int), "Key must be int: event_key"
        for name in ("session", "username"):
            assert isinstance(record[name], str), "Key must be string: %r" % name
        now = time.time()
        self.conn.execute(
            "insert or replace into events values (?, ?, ?, ?, ?, ?, ?)",
            (
                "%s-%s-%i" % (record["username"], record["session"], record["event_key"]),
                record["event_key"],
                record["session"],
                record["username"],
                json.dumps(record["event_data"]),
                json.dumps(logging_context),
                now,
            ),
        )
        self.conn.commit()

db = BigBrotherDB()

class HeadersMixin:
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def require_credentials(self, payload):
        print("Credentials check on:", payload["username"], payload["token"], self.request)
        if not db.credential_check(payload["username"], payload["token"]):
            self.write(json.dumps({"success": False}))
            raise tornado.web.HTTPError(status_code=401)

    def options(self):
        self.set_status(204)
        self.finish()

class HealthHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Good")

class LoginHandler(HeadersMixin, tornado.web.RequestHandler):
    def post(self):
        payload = json.loads(self.request.body)
        check = db.credential_check(payload["username"], payload["token"])
        # If we don't know about this user, then create them.
        if check is None:
            db.create_user(payload["username"], payload["token"])
            success = True
        else:
            success = check
        self.write(json.dumps({"success": success}))

class WriteHandler(HeadersMixin, tornado.web.RequestHandler):
    def post(self):
        payload = json.loads(self.request.body)
        self.require_credentials(payload)
        logging_context = {
            #"request": repr(self.request),
            "time": time.time(),
        }
        # Write a collection of events.
        for event_key, event_data in payload["events"].items():
            event_key = int(event_key)
            db.insert_row(
                record={
                    "event_key": event_key,
                    "session": payload["session"],
                    "username": payload["username"],
                    "event_data": event_data,
                },
                logging_context=logging_context,
            )
        self.write(json.dumps({"success": True}))

class ReadHandler(HeadersMixin, tornado.web.RequestHandler):
    def get(self):
        payload = json.loads(self.request.body)
        #self.require_credentials(payload)
        result = list(db.get_events(payload["username"]))
        self.write(json.dumps({"success": True, "events": result}))

def make_app():
    return tornado.web.Application([
        ("/health", HealthHandler),
        ("/login", LoginHandler),
        ("/write", WriteHandler),
        #("/read", ReadHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(1234)
    tornado.ioloop.IOLoop.current().start()

