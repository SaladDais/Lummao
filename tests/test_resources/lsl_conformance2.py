from lummao import *


class Script(BaseLSLScript):
    gTestsPassed: int
    gTestsFailed: int
    gNullKey: Key
    gStringInAKey: Key
    gKeyInAString: str
    gVisitedStateTest: int
    chat: int
    gVector: Vector

    def __init__(self):
        super().__init__()
        self.gTestsPassed = 0
        self.gTestsFailed = 0
        self.gNullKey = typecast("00000000-0000-0000-0000-000000000000", Key)
        self.gStringInAKey = typecast("foo", Key)
        self.gKeyInAString = typecast(self.gNullKey, str)
        self.gVisitedStateTest = 0
        self.chat = 1
        self.gVector = Vector((0.0, 0.0, 0.0))

    def testPassed(self, description: str, actual: str, expected: str) -> None:
        self.gTestsPassed += 1

    def testFailed(self, description: str, actual: str, expected: str) -> None:
        self.gTestsFailed += 1
        print(radd(")", radd(expected, radd(" expected ", radd(actual, radd(" (", radd(description, "FAILED!: ")))))))
        self.builtin_funcs.llOwnerSay(typecast(rdiv(0, 0), str))

    def ensureTrue(self, description: str, actual: int) -> None:
        if cond(actual):
            self.testPassed(description, typecast(actual, str), typecast(1, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(1, str))

    def ensureFalse(self, description: str, actual: int) -> None:
        if cond(actual):
            self.testFailed(description, typecast(actual, str), typecast(0, str))
        else:
            self.testPassed(description, typecast(actual, str), typecast(0, str))

    def ensureIntegerEqual(self, description: str, actual: int, expected: int) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def floatEqual(self, actual: float, expected: float) -> int:
        error: float = self.builtin_funcs.llFabs(rsub(actual, expected))
        epsilon: float = bin2float('0.001000', '6f12833a')
        if cond(rgreater(epsilon, error)):
            self.builtin_funcs.llSay(0, radd(typecast(error, str), "Float equality delta "))
            return 0
        return 1

    def ensureFloatEqual(self, description: str, actual: float, expected: float) -> None:
        if cond(self.floatEqual(actual, expected)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def ensureFloatExactEqual(self, description: str, actual: float, expected: float) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def ensureStringEqual(self, description: str, actual: str, expected: str) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def ensureKeyEqual(self, description: str, actual: Key, expected: Key) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def ensureVectorEqual(self, description: str, actual: Vector, expected: Vector) -> None:
        if cond(rbooland(self.floatEqual(actual[2], expected[2]), rbooland(self.floatEqual(actual[1], expected[1]), self.floatEqual(actual[0], expected[0])))):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def ensureRotationEqual(self, description: str, actual: Quaternion, expected: Quaternion) -> None:
        if cond(rbooland(self.floatEqual(actual[3], expected[3]), rbooland(self.floatEqual(actual[2], expected[2]), rbooland(self.floatEqual(actual[1], expected[1]), self.floatEqual(actual[0], expected[0]))))):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def ensureListEqual(self, description: str, actual: list, expected: list) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    def testReturnFloat(self) -> float:
        return 1.0

    def testReturnKey(self) -> Key:
        return typecast("00000000-0000-0000-0000-000000000000", Key)

    def testArgumentAccessor(self, v: Vector) -> None:
        v = Vector((0.0, 0.0, 0.0))
        v = replace_coord_axis(v, 0, self.testReturnFloat())
        v = replace_coord_axis(v, 1, self.testReturnFloat())
        v = replace_coord_axis(v, 2, self.testReturnFloat())
        self.ensureVectorEqual("testArgumentAccessor", v, Vector((1.0, 1.0, 1.0)))

    def testLocalAccessor(self) -> None:
        v: Vector = Vector((0.0, 0.0, 0.0))
        v = replace_coord_axis(v, 0, self.testReturnFloat())
        v = replace_coord_axis(v, 1, self.testReturnFloat())
        v = replace_coord_axis(v, 2, self.testReturnFloat())
        self.ensureVectorEqual("testLocalAccessor", v, Vector((1.0, 1.0, 1.0)))

    def testGlobalAccessor(self) -> None:
        self.gVector = Vector((0.0, 0.0, 0.0))
        self.gVector = replace_coord_axis(self.gVector, 0, self.testReturnFloat())
        self.gVector = replace_coord_axis(self.gVector, 1, self.testReturnFloat())
        self.gVector = replace_coord_axis(self.gVector, 2, self.testReturnFloat())
        self.ensureVectorEqual("testGlobalAccessor", self.gVector, Vector((1.0, 1.0, 1.0)))

    def tests(self) -> None:
        self.ensureTrue("gVisitedStateTest ", self.gVisitedStateTest)
        self.ensureFloatExactEqual("1.4e-45 == (float)\"1.4e-45\"", bin2float('0.000000', '01000000'), typecast("1.4e-45", float))
        self.testArgumentAccessor(Vector((0.0, 0.0, 0.0)))
        self.testLocalAccessor()
        self.testGlobalAccessor()
        self.ensureStringEqual("(string)[1, testReturnFloat(), testReturnFloat()] == \"11.01.0\"", typecast([1, self.testReturnFloat(), self.testReturnFloat()], str), "11.0000001.000000")
        k: Key = typecast("foo", Key)
        k2: Key = typecast("foo", Key)
        self.ensureKeyEqual("k = \"foo\";k2 = \"foo\";k == k2", k, k2)
        self.ensureIntegerEqual("[] == []", req([], []), 1)
        self.ensureIntegerEqual("[1] == [2]", req([2], [1]), 1)
        self.ensureIntegerEqual("[1,2] == [1,2]", req([1, 2], [1, 2]), 1)
        self.ensureIntegerEqual("[1,2] == [2]", req([2], [1, 2]), 0)
        self.ensureIntegerEqual("[1] == [2,3]", req([2, 3], [1]), 0)
        self.ensureIntegerEqual("[] != []", rneq([], []), 0)
        self.ensureIntegerEqual("[1] != [2]", rneq([2], [1]), 0)
        self.ensureIntegerEqual("[1,2] != [1,2]", rneq([1, 2], [1, 2]), 0)
        self.ensureIntegerEqual("[1,2] != [2]", rneq([2], [1, 2]), 1)
        self.ensureIntegerEqual("[1] != [2,3]", rneq([2, 3], [1]), -1)
        self.ensureFloatEqual("(float)\"5.0a\" == 5.0", typecast("5a", float), 5.0)
        self.ensureFloatEqual("(integer)\"12foo\" == 12", float(typecast("12foo", int)), 12.0)
        l: list = []
        l = [42]
        radd(1, l)
        self.ensureListEqual("list l = [42]; l + 1; l == [42]", l, [42])
        l = [42]
        radd(bin2float('1.500000', '0000c03f'), l)
        self.ensureListEqual("list l = [42]; l + 1.5; l == [42]", l, [42])
        l = [42]
        radd("00000000-0000-0000-0000-000000000000", l)
        self.ensureListEqual("list l = [42]; l + NULL_KEY; l == [42]", l, [42])
        l = [42]
        radd(Vector((1.0, 2.0, 3.0)), l)
        self.ensureListEqual("list l = [42]; l + <1,2,3>; l == [42]", l, [42])
        l = [42]
        radd(Quaternion((1.0, 2.0, 3.0, 4.0)), l)
        self.ensureListEqual("list l = [42]; l + <1,2,3>; l == [42]", l, [42])
        if cond(k):
            self.testFailed("if(k)", "TRUE", "FALSE")
        else:
            self.testPassed("if(k)", "FALSE", "FALSE")
        self.ensureIntegerEqual("k == \"foo\"", req("foo", k), 1)
        self.ensureIntegerEqual("gStringInAKey == \"foo\"", req("foo", self.gStringInAKey), 1)
        self.ensureIntegerEqual("gNullKey == NULL_KEY", req("00000000-0000-0000-0000-000000000000", self.gNullKey), 1)
        k = typecast("00000000-0000-0000-0000-000000000000", Key)
        s: str = ""
        s = typecast(k, str)
        self.ensureStringEqual("k = NULL_KEY; string s; s = k;", s, "00000000-0000-0000-0000-000000000000")
        v: Vector = Vector((1.0, 1.0, 1.0))
        while cond(v):
            v = Vector((0.0, 0.0, 0.0))
        self.ensureVectorEqual("while (v) { v = ZERO_VECTOR; }", v, Vector((0.0, 0.0, 0.0)))
        v = Vector((2.0, 2.0, 2.0))
        while True == True:
            v = Vector((0.0, 0.0, 0.0))
            if not cond(v):
                break
        self.ensureVectorEqual("v = <2,2,2>; do { v = ZERO_VECTOR } while (v);", v, Vector((0.0, 0.0, 0.0)))
        v = Vector((3.0, 3.0, 3.0))
        while True == True:
            if not cond(v):
                break
            pass
            v = Vector((0.0, 0.0, 0.0))
        self.ensureVectorEqual("for (v = <3,3,3>;v;v=ZERO_VECTOR) {}", v, Vector((0.0, 0.0, 0.0)))
        k = typecast("7c42811e-229f-4500-b6d7-2c37324ff816", Key)
        while cond(k):
            k = typecast("00000000-0000-0000-0000-000000000000", Key)
        self.ensureKeyEqual("while (k) { k = NULL_KEY; }", k, typecast("00000000-0000-0000-0000-000000000000", Key))
        k = typecast("7c42811e-229f-4500-b6d7-2c37324ff816", Key)
        while True == True:
            k = typecast("00000000-0000-0000-0000-000000000000", Key)
            if not cond(k):
                break
        self.ensureKeyEqual("k = \"7c42811e-229f-4500-b6d7-2c37324ff816\"; do { k = NULL_KEY } while (k);", k, typecast("00000000-0000-0000-0000-000000000000", Key))
        k = typecast("7c42811e-229f-4500-b6d7-2c37324ff816", Key)
        while True == True:
            if not cond(k):
                break
            pass
            k = typecast("00000000-0000-0000-0000-000000000000", Key)
        self.ensureKeyEqual("for (k = \"7c42811e-229f-4500-b6d7-2c37324ff816\";k;k=NULL_KEY) {}", k, typecast("00000000-0000-0000-0000-000000000000", Key))
        q: Quaternion = Quaternion((1.0, 1.0, 1.0, 1.0))
        while cond(q):
            q = Quaternion((0.0, 0.0, 0.0, 1.0))
        self.ensureRotationEqual("while (q) { q = ZERO_ROTATION; }", q, Quaternion((0.0, 0.0, 0.0, 1.0)))
        q = Quaternion((2.0, 2.0, 2.0, 2.0))
        while True == True:
            q = Quaternion((0.0, 0.0, 0.0, 1.0))
            if not cond(q):
                break
        self.ensureRotationEqual("q = <2,2,2>; do { v = ZERO_ROTATION } while (q);", q, Quaternion((0.0, 0.0, 0.0, 1.0)))
        q = Quaternion((3.0, 3.0, 3.0, 3.0))
        while True == True:
            if not cond(q):
                break
            pass
            q = Quaternion((0.0, 0.0, 0.0, 1.0))
        self.ensureRotationEqual("for (q = <3,3,3,3>;q;q=ZERO_ROTATION) {}", q, Quaternion((0.0, 0.0, 0.0, 1.0)))
        l = [1]
        l = [2]
        while True == True:
            l = []
            if not cond(l):
                break
        self.ensureListEqual("l = [2]; do { v = [] } while (l);", l, [])
        s = "1!"
        while cond(s):
            s = ""
        self.ensureStringEqual("while (s) { s = \"\"; }", s, "")
        s = "2!"
        while True == True:
            s = ""
            if not cond(s):
                break
        self.ensureStringEqual("s = \"2!\"; do { s = \"\" } while (s);", s, "")
        s = "3!"
        while True == True:
            if not cond(s):
                break
            pass
            s = ""
        self.ensureStringEqual("for (s = \"3!\";s;s=\"\") {}", s, "")
        i: int = 1
        while cond(i):
            i = 0
        self.ensureIntegerEqual("while (i) { i = 0; }", i, 0)
        i = 2
        while True == True:
            i = 0
            if not cond(i):
                break
        self.ensureIntegerEqual("i = 2; do { i = 0 } while (i);", i, 0)
        i = 3
        while True == True:
            if not cond(i):
                break
            pass
            i = 0
        self.ensureIntegerEqual("for (i = 3;i;i=0) {}", i, 0)
        f: float = 1.0
        while cond(f):
            f = 0.0
        self.ensureFloatEqual("while (f) { f = 0; }", f, 0.0)
        f = 2.0
        while True == True:
            f = 0.0
            if not cond(f):
                break
        self.ensureFloatEqual("f = 2; do { f = 0 } while (f);", f, 0.0)
        f = 3.0
        while True == True:
            if not cond(f):
                break
            pass
            f = 0.0
        self.ensureFloatEqual("for (f = 3;f;f=0) {}", f, 0.0)
        v = Vector((1.0, 2.0, 3.0))
        v = rmul(2.0, v)
        self.ensureVectorEqual("v = <1,2,3>; v *= 2;", v, Vector((2.0, 4.0, 6.0)))
        v = Vector((1.0, 2.0, 3.0))
        v = rmul(bin2float('0.500000', '0000003f'), v)
        self.ensureVectorEqual("v = <1,2,3>; v *= 0.5;", v, Vector((bin2float('0.500000', '0000003f'), 1.0, bin2float('1.500000', '0000c03f'))))
        v = Vector((1.0, 0.0, 0.0))
        v = rmul(Quaternion((0.0, 0.0, 0.0, 1.0)), v)
        self.ensureVectorEqual("vector v = <1,0,0>; v *= ZERO_ROTATION;", v, Vector((1.0, 0.0, 0.0)))
        v = Vector((0.0, 1.0, 0.0))
        v = rmod(Vector((0.0, 0.0, 1.0)), v)
        self.ensureVectorEqual("vector v = <0,1,0>; v %= <0,0,1>;", v, Vector((1.0, 0.0, 0.0)))
        r: Quaternion = Quaternion((0.0, 0.0, 0.0, 1.0))
        r = rmul(Quaternion((0.0, 0.0, 0.0, 1.0)), r)
        self.ensureRotationEqual("rotation r = ZERO_ROTATION; r *= ZERO_ROTATION;", r, Quaternion((0.0, 0.0, 0.0, 1.0)))
        self.ensureStringEqual("(string)-0.0", typecast(-0.0, str), "-0.000000")
        self.ensureStringEqual("(string)<-0.0,0.0,-0.0>", typecast(Vector((-0.0, 0.0, -0.0)), str), "<-0.00000, 0.00000, -0.00000>")
        self.ensureStringEqual("(string)<-0.0,0.0,-0.0,0.0>", typecast(Quaternion((-0.0, 0.0, -0.0, 0.0)), str), "<-0.00000, 0.00000, -0.00000, 0.00000>")
        self.ensureStringEqual("llList2CSV([-0.0, <-0.0,0.0,-0.0>, <-0.0,0.0,-0.0,0.0>])", self.builtin_funcs.llList2CSV([-0.0, Vector((-0.0, 0.0, -0.0)), Quaternion((-0.0, 0.0, -0.0, 0.0))]), "-0.000000, <-0.000000, 0.000000, -0.000000>, <-0.000000, 0.000000, -0.000000, 0.000000>")
        self.ensureStringEqual("llDumpList2String([-0.0, <-0.0,0.0,-0.0>, <-0.0,0.0,-0.0,0.0>], \" ~ \")", self.builtin_funcs.llDumpList2String([-0.0, Vector((-0.0, 0.0, -0.0)), Quaternion((-0.0, 0.0, -0.0, 0.0))], " ~ "), "0.000000 ~ <0.000000, 0.000000, 0.000000> ~ <0.000000, 0.000000, 0.000000, 0.000000>")
        self.ensureStringEqual("(string)[-0.0, <-0.0,0.0,-0.0>, <-0.0,0.0,-0.0,0.0>]", typecast([-0.0, Vector((-0.0, 0.0, -0.0)), Quaternion((-0.0, 0.0, -0.0, 0.0))], str), "-0.000000<-0.000000, 0.000000, -0.000000><-0.000000, 0.000000, -0.000000, 0.000000>")
        self.ensureStringEqual("llList2String([-0.0], 0)", self.builtin_funcs.llList2String([-0.0], 0), "-0.000000")
        self.ensureStringEqual("(string)(float)\"-0.0\"", typecast(typecast("-0.0", float), str), "-0.000000")
        self.ensureStringEqual("(string)(vector)\"<-0.0,0.0,-0.0>\"", typecast(typecast("<-0.0,0.0,-0.0>", Vector), str), "<-0.00000, 0.00000, -0.00000>")
        self.ensureStringEqual("(string)(rotation)\"<-0.0,0.0,-0.0,0.0>\"", typecast(typecast("<-0.0,0.0,-0.0,0.0>", Quaternion), str), "<-0.00000, 0.00000, -0.00000, 0.00000>")
        self.ensureKeyEqual("testReturnKey() == NULL_KEY", self.testReturnKey(), typecast("00000000-0000-0000-0000-000000000000", Key))
        defaultKey: Key = Key("")
        self.ensureKeyEqual("key defaultKey;", defaultKey, typecast("", Key))
        defaultInteger: int = 0
        self.ensureIntegerEqual("key defaultInteger;", defaultInteger, 0)
        defaultFloat: float = 0.0
        self.ensureFloatEqual("key defaultInteger;", defaultFloat, 0.0)
        defaultString: str = ""
        self.ensureStringEqual("string defaultString;", defaultString, "")
        self.ensureIntegerEqual("chat == TRUE", self.chat, 1)

    def runTests(self) -> None:
        self.gTestsPassed = 0
        self.gTestsFailed = 0
        self.tests()
        self.gVisitedStateTest = 0
        print("Test succeeded")

    def edefaultstate_entry(self) -> None:
        raise StateChangeException('StateTest')

    def edefaulttouch_start(self, total_number: int) -> None:
        raise StateChangeException('StateTest')

    def eStateTeststate_entry(self) -> None:
        self.ensureFalse("gVisitedStateTest", self.gVisitedStateTest)
        self.gVisitedStateTest = 1
        self.runTests()

    def eStateTesttouch_start(self, total_number: int) -> None:
        raise StateChangeException('default')

