default {
    state_entry() {
        jump foo;
        rotation q;
        integer i;
        @foo;
        // we should have jumped over the initializer, leaving w / s as 0.
        if (q != <0, 0, 0, 0> || i != 0) {
            0/0;
        }
    }
}