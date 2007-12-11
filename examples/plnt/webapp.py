# -*- coding: utf-8 -*-
"""
    plnt.webapp
    ~~~~~~~~~~~

    The web part of the planet.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: BSD.
"""
from os import path
from sqlalchemy import create_engine
from werkzeug import SharedDataMiddleware, append_slash_redirect
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import RequestRedirect
from plnt.utils import Request, local, local_manager, url_map, endpoints
from plnt.database import metadata

# import the views module because it contains setup code
import plnt.views

#: path to shared data
SHARED_DATA = path.join(path.dirname(__file__), 'shared')


class Plnt(object):

    def __init__(self, database_uri):
        self.database_engine = create_engine(database_uri)

        self._dispatch = local_manager.middleware(self.dispatch_request)
        self._dispatch = SharedDataMiddleware(self._dispatch, {
            '/shared':      SHARED_DATA
        })

    def init_database(self):
        metadata.create_all(self.database_engine)

    def bind_to_context(self):
        local.application = self

    def dispatch_request(self, environ, start_response):
        self.bind_to_context()
        local.request = request = Request(environ, start_response)
        local.url_adapter = adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match(request.path)
            response = endpoints[endpoint](request, **values)
        except (RequestRedirect, HTTPException), e:
            response = e
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self._dispatch(environ, start_response)