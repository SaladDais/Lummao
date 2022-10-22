#!/usr/bin/env python
"""
Run an LSL webserver under Python using Quart and Werkzeug

Unlike regular LSL, this allows multiple requests to be handled
simultaneously. Be careful to add guards around your critical sections,
or you'll get nasty concurrency bugs. Enjoy those.
"""

import asyncio
import dataclasses
import os
import sys
import uuid
from typing import Dict

from quart import Quart, Request, Response, request
from werkzeug.datastructures import Headers

import lummao
from lummao import Key, BaseLSLScript


@dataclasses.dataclass
class RequestData:
    request: Request
    resp_fut: asyncio.Future[Response] = dataclasses.field(default_factory=asyncio.Future)
    req_headers: Headers = dataclasses.field(default_factory=Headers)
    content_type: str = "text/plain"


class LSLWSGIWrapper:
    script: BaseLSLScript

    def __init__(self, script: BaseLSLScript):
        self.script: BaseLSLScript = script
        self._pending_requests: Dict[Key, RequestData] = dict()

        script.builtin_funcs["llRequestURL"] = self._handle_url_request
        script.builtin_funcs["llRequestSecureURL"] = self._handle_url_request
        script.builtin_funcs["llOwnerSay"] = print
        script.builtin_funcs["llSetContentType"] = self._set_content_type
        script.builtin_funcs["llGetHTTPHeader"] = self._get_header
        script.builtin_funcs["llHTTPResponse"] = self._set_http_response
        script.builtin_funcs["llSleep"] = asyncio.sleep

    def _handle_url_request(self):
        request_id = Key(uuid.uuid4())
        self.script.queue_event("http_request", (request_id, "URL_REQUEST_GRANTED", _get_server_url()))
        return request_id

    def _set_content_type(self, req_id: Key, content_type: str):
        if req_id not in self._pending_requests:
            return
        self._pending_requests[req_id].content_type = content_type

    def _get_header(self, req_id: Key, header_name: str):
        if req_id not in self._pending_requests:
            return ""
        return self._pending_requests[req_id].req_headers.get(header_name, "")

    def _set_http_response(self, req_id: Key, status_code: int, body: str):
        if req_id not in self._pending_requests:
            return
        req_data = self._pending_requests[req_id]
        resp = Response(body, status_code, content_type=req_data.content_type)
        req_data.resp_fut.set_result(resp)

    async def execute(self):
        await self.script.execute()

    async def handle_request(self):
        # LSL has a bunch of special internally-meaningful HTTP methods that shouldn't
        # be allowed in from the outside, like the URL grant ones. Whitelist HTTP methods.
        if request.method.upper() not in {"POST", "GET", "OPTIONS", "PATCH", "PUT", "DELETE"}:
            return Response("Unacceptable method", status=400)

        req_id = Key(uuid.uuid4())
        req_data = RequestData(request)
        req_data.req_headers.update(request.headers)
        req_data.req_headers["x-path-info"] = request.path
        req_data.req_headers["x-query-string"] = request.query_string.decode("utf8")
        req_data.req_headers["x-script-url"] = _get_server_url()
        req_data.req_headers["x-remote-ip"] = request.remote_addr
        self._pending_requests[req_id] = req_data

        str_body = (await request.data).decode("utf8")
        self.script.queue_event("http_request", (req_id, request.method, str_body))

        try:
            # Remember, the script responds by calling llHttpResponse(), and may leave
            # the event handler without ever calling it. It may also sleep for a long time
            # after responding. Handle that by kicking off an async task. Handler execution
            # won't die with the connection!
            asyncio.create_task(self.script.execute())
            # Wait 30 seconds for the request to be handled, then bail.
            return await asyncio.wait_for(req_data.resp_fut, timeout=30.0)
        except asyncio.TimeoutError:
            return Response("Request timed out", status=408)
        finally:
            self._pending_requests.pop(req_id)


def _get_server_port():
    return int(os.environ.get("SERVER_PORT", "5001"))


def _get_server_url():
    proto = str(os.environ.get("SERVER_PROTO", "http"))
    host = os.environ.get("SERVER_NAME", "localhost")
    port = _get_server_port()
    url = f"{proto}://{host}"
    if port:
        return f"{url}:{port}"
    return url


def main():
    loop = asyncio.get_event_loop_policy().get_event_loop()
    wrapped = LSLWSGIWrapper(lummao.compile_script_file(sys.argv[1]))
    # Let LSL stand itself up and figure out its URL
    loop.run_until_complete(wrapped.execute())

    app = Quart(__name__)
    # This essentially bypasses Quart's routing and passes every request to LSL
    app.before_request(wrapped.handle_request)
    # Can't use reloader because it tries to reload the LSL!
    app.run(
        host=os.environ.get("SERVER_NAME", "localhost"),
        port=_get_server_port(),
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
