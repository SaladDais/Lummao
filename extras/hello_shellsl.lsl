#!/usr/local/bin/shellsl
// obviously, shellsl has to be placed here for the shebang to work.

default {
    state_entry() {
        llOwnerSay("Hello, " + exec(["whoami"]) + ", you're quite good at turning me on");
        llOwnerSay(llList2String(argv, 1));
    }
}
