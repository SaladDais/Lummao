default
{
    state_entry()
    {
        integer i;
        for(i=0; i<2; ++i) {
            // jump over the initializer on the second loop
            if (i > 0)
                jump baz;
            string foo;
            // make sure it's not just the declaration getting hoisted
            foo = "quux";
            @baz;
            // should say "quux" both times because the locals slot was
            // not actually cleared at the start / exit of the loop.
            llOwnerSay(foo);
        }
    }
}
