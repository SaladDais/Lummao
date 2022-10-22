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
            string path = llGetHTTPHeader(id, "x-path-info");
            if (path == "/timeout")
                return;

            if (path == "/lazy") {
                llSleep(5.0);
            }

            list headerList = ["x-script-url", "x-path-info", "x-query-string", "x-remote-ip", "user-agent"];

            integer index = -llGetListLength(headerList);
            do {
                string header = llList2String(headerList, index);
                llOwnerSay(header + ": " + llGetHTTPHeader(id, header));
            } while (++index);

            llOwnerSay("body:\n" + body);
            llHTTPResponse(id, 200, "I live at " + gURL + " and I've served " + (string)gRequests + " requests!");

            if (path == "/lazy_after")
                llSleep(5.0);
            llOwnerSay("Finished " + (string)id);
        }
    }
}
