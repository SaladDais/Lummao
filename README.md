# Lummao

[Lummao](https://github.com/SaladDais/Lummao) is a toolkit for compiling and executing the Linden Scripting Language as Python. 
It aims to ease testing of LSL code by leveraging Python's existing ecosystem for debugging and testing. Think of it as the less opinionated,
stupider cousin of [LSLForge's unit testing framework](https://github.com/raysilent/lslforge/blob/master/lslforge/eclipse/lslforge/html/unit-test.html).

It could conceivably be used for compile-time evaluation of pure functions with statically known arguments.

The runtime is largely handled by the excellent implementation of LSL's basic operations and library functions
from [LSL-PyOptimizer](https://github.com/Sei-Lisa/LSL-PyOptimizer).

To see an example input script and its Python output, see the [`test_resources` directory](https://github.com/SaladDais/Lummao/tree/master/tests/test_resources).

## Setup

LSL PyOptimizer is not distributed in a form that would allow easily using it as a library, it must be installed separately,
with an environment variable pointing to its location so Lummao can find it.

* Download <https://github.com/Sei-Lisa/LSL-PyOptimizer>
* Create a new environment variable named `LSL_PYOPTIMIZER_PATH` and set its value to the the path you placed LSL-PyOptimizer in
* Download <https://github.com/SaladDais/tailslide> and follow the compilation instructions, doing `make install` at the end
* Download <https://github.com/SaladDais/Lummao>
* `pip install -e .`
* You can now use `lummao` to transpile an LSL script to a Python script.
* Hooray

## Why

If you've ever written a sufficiently complicated system in LSL, you know how annoying it is to debug your scripts
or be sure if they're even correct. Clearly the sanest way to bring sanity to your workflow is to convert your LSL
scripts to Python, so you can mock LSL library functions and use Python debuggers. Hence the name "Lummao".

## TODO

* Use LSL-PyOptimizer's `lslparse` / `lsloutput` stuff rather than rely on native code for transpilation
* * Just used Tailslide since it was easier for me to get started with it.
* Symbol shadowing behavior is not correct
* The behavior of variables whose declarations are `jump`ed over is not correct
* Provide mock helpers for: 
* * inter-script communication
* * HTTP
* * auto-stubs for all functions
* * state-aware event queueing (and state switching, for that matter)

## License

GPLv3

### Licensing Clarifications

The output of the compiler necessarily links against the GPL-licensed runtime code from LSL-PyOptimizer for
functionality, and LSL-PyOptimizer does not provide a library exception in its license.
You should assume that any LSL converted to Python by the compiler and any testcases you write exercising
them must _also_ be distributable under the GPL.

In short: If or when you distribute your testcases, you must _also_ allow distribution of their direct
dependencies (your LSL scripts) under the terms of the GPL. This does not necessarily
change the license of your LSL scripts themselves, or require consumers of your scripts to license
their own scripts under the GPL. It is perfectly possible to have an otherwise MIT-licensed or proprietary
library with a GPL-licensed test suite. No distribution of testcases == no requirement to distribute under the GPL.

Suggested reading to understand your rights and obligations under the GPL when using a GPL-licensed test suite:

* https://www.gnu.org/licenses/gpl-3.0.html
* https://opensource.stackexchange.com/questions/7503/implications-of-using-gpl-licenced-code-only-during-testing
* https://opensource.stackexchange.com/questions/4112/using-gpl-library-in-unit-test-suite-of-open-source-library
