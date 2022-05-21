key gURLRequest;
string gURL;
integer gRequests;

default {
    state_entry() {
        gURLRequest = llRequestURL();
    }

    http_request(key id, string method, string body) {
        if (gURLRequest == id) {
            if (method == URL_REQUEST_GRANTED) {
                gURL = body;
                llOwnerSay("Got our URL: " + gURL);
            }
        } else {
            ++gRequests;
            list headerList = ["x-script-url", "x-path-info", "x-query-string", "x-remote-ip", "user-agent"];

            integer index = -llGetListLength(headerList);
            do {
                string header = llList2String(headerList, index);
                llOwnerSay(header + ": " + llGetHTTPHeader(id, header));
            } while (++index);

            llOwnerSay("body:\n" + body);
            llHTTPResponse(id, 200, "I live at " + gURL + " and I've served " + (string)gRequests + " requests!");
        }
    }
}
