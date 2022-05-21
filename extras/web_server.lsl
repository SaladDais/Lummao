key url_request;

default {
    state_entry() {
        url_request = llRequestURL();
    }

    http_request(key id, string method, string body) {
        if (url_request == id) {
            if (method == URL_REQUEST_GRANTED)
                llOwnerSay("Got our URL: " + body);
        } else {
            list headerList = ["x-script-url", "x-path-info", "x-query-string", "x-remote-ip", "user-agent"];

            integer index = -llGetListLength(headerList);
            do {
                string header = llList2String(headerList, index);
                llOwnerSay(header + ": " + llGetHTTPHeader(id, header));
            } while (++index);

            llOwnerSay("body:\n" + body);
            llHTTPResponse(id, 200, "Hey here's the stuff you sent me:\n" + body);
        }
    }
}
