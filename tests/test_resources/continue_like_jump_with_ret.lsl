float foo() {
    integer i;
    while (++i < 10) {
        if (1)
            jump foo;
        return 1.0;
        @foo;
    }
    return 2.0;
}

default {
    state_entry() {
        if (foo() != 2.0)
            0/0;
    }
}
