#!/usr/bin/env shellsl
// The shebang should allow executing LSL files directly!

default {
    state_entry() {
        llOwnerSay("Hello, " + exec(["whoami"]) + ", you're quite good at turning me on");
        llOwnerSay(llList2String(argv, 1));
    }
}
