#!/usr/bin/env python
import dataclasses
import os
import sys
import uuid
from subprocess import Popen, PIPE
from typing import Dict

from werkzeug import Request, run_simple, Response
from werkzeug.datastructures import Headers

from lummao import Key, BaseLSLScript


def _compile_script_bytes(lsl_bytes):
    p = Popen(['lummao', '-', '-'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    output, errors = p.communicate(input=lsl_bytes)
    if p.returncode:
        if errors:
            print(errors.decode("utf8"), file=sys.stderr)
        sys.exit(1)
    new_globals = globals().copy()
    exec(output, new_globals)
    return new_globals["Script"]()


@dataclasses.dataclass
class RequestData:
    request: Request
    resp_body: str = ""
    resp_status: int = 500
    req_headers: Headers = dataclasses.field(default_factory=Headers)
    content_type: str = "text/plain"


class LSLWSGIWrapper:
    script: BaseLSLScript

    def __init__(self, script: BaseLSLScript):
        script.builtin_funcs["llRequestURL"] = self._handle_url_request
        script.builtin_funcs["llRequestSecureURL"] = self._handle_url_request
        script.builtin_funcs["llOwnerSay"] = print
        script.builtin_funcs["llSetContentType"] = self._set_content_type
        script.builtin_funcs["llGetHTTPHeader"] = self._get_header
        script.builtin_funcs["llHTTPResponse"] = self._set_http_response
        self.script: BaseLSLScript = script
        self._pending_requests: Dict[Key, RequestData] = dict()

    def _handle_url_request(self):
        request_id = Key(uuid.uuid4())
        self.script.queue_event("http_request", (request_id, "URL_REQUEST_GRANTED", _get_url()))
        return request_id

    def _set_content_type(self, req_id: Key, content_type: str):
        self._pending_requests[req_id].content_type = content_type

    def _get_header(self, req_id: Key, header_name: str):
        return self._pending_requests[req_id].req_headers.get(header_name, "")

    def _set_http_response(self, req_id: Key, status_code: int, body: str):
        req_data = self._pending_requests[req_id]
        req_data.resp_status = status_code
        req_data.resp_body = body

    def execute(self):
        self.script.execute()

    @Request.application
    def handle_request(self, request: Request):
        req_id = Key(uuid.uuid4())
        req_data = RequestData(request)
        req_data.req_headers.update(request.headers)
        req_data.req_headers["x-path-info"] = request.path
        req_data.req_headers["x-query-string"] = request.query_string.decode("utf8")
        req_data.req_headers["x-script-url"] = _get_url()
        req_data.req_headers["x-remote-ip"] = request.remote_addr
        self._pending_requests[req_id] = req_data
        self.script.queue_event("http_request", (req_id, request.method, request.data.decode("utf8")))
        # OK, so this isn't an exact model of how HTTP-in works. Who cares.
        self.script.execute()
        self._pending_requests.pop(req_id)
        # This uhhhhh is not actually asynchronous, but I guess it could be made async.
        return Response(req_data.resp_body, req_data.resp_status, content_type=req_data.content_type)


def _get_port():
    return int(os.environ.get("SERVER_PORT", "5001"))


def _get_url():
    proto = str(os.environ.get("SERVER_PROTO", "http"))
    host = os.environ.get("SERVER_NAME", "localhost")
    port = _get_port()
    url = f"{proto}://{host}"
    if port:
        return f"{url}:{port}"
    return url


def main():
    lsl_file = sys.argv[1]
    with open(lsl_file, "rb") as f:
        lsl_bytes = f.read()
    wrapped = LSLWSGIWrapper(_compile_script_bytes(lsl_bytes))
    # Let LSL stand itself up and figure out its URL
    wrapped.execute()
    run_simple(os.environ.get("SERVER_NAME", "localhost"), _get_port(), wrapped.handle_request)


if __name__ == "__main__":
    main()
