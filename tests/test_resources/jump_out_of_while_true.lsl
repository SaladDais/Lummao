default {
    state_entry() {
        while (TRUE)
            jump foo;
        @foo;
    }
}
