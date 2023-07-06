string gResp;
integer gTriggered;
key gRequestID;

makeRequest(string url) {
    gRequestID = llHTTPRequest(url, [
        HTTP_METHOD, "GET",
        HTTP_CUSTOM_HEADER, "Foo", "Bar"
    ], "");
}

default {
    http_response(key request_id, integer status, list meta, string body) {
        gTriggered = TRUE;
        if (request_id != gRequestID) {
            // request ID should always match
            llOwnerSay((string)(0/0));
        }
        gResp = body;
    }
}
