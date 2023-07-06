integer gCount = 0;

default {
    state_entry() {
        llSetTimerEvent(0.01);
    }

    timer() {
        if (++gCount >= 3) {
            llSetTimerEvent(0);
        }
    }
}
