import logging
import uuid

import aiohttp

from . import Key
from .lslexecutils import ScriptExtender, BaseLSLScript


HTTP_METHOD = 0
HTTP_CUSTOM_HEADER = 5

STATUS_INTERNAL_ERROR = 499  # "Wire chewed by rabbit"


class HTTPRequestScriptExtender(ScriptExtender):
    def extend_script(self, script: BaseLSLScript):
        super().extend_script(script)
        self.script.builtin_funcs["llHTTPRequest"] = self._http_request

    async def _http_request(self, url: str, options: list, body: str) -> Key:
        request_id = Key(str(uuid.uuid4()))

        method = "GET"
        headers = {}
        while options:
            key = options.pop(0)
            if key == HTTP_METHOD:
                method = options.pop(0)
            elif key == HTTP_CUSTOM_HEADER:
                key = options.pop(0)
                headers[key] = options.pop(0)
            else:
                raise ValueError(key)

        # Perform the request in the background
        self.create_publisher_task(self._perform_request(request_id, method, url, headers, body))

        return request_id

    async def _perform_request(self, request_id: Key, method: str, url: str, headers: dict, body: str) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, data=body, headers=headers) as resp:
                    resp_body = await resp.text()
                    self.script.queue_event("http_response", (request_id, resp.status, [], resp_body), None)
        except:  # noqa: Swallowing exceptions is intentional here
            logging.exception("Internal error while handling HTTP")
            self.script.queue_event(
                "http_response",
                (request_id, STATUS_INTERNAL_ERROR, [], "Internal exception"),
                None
            )
