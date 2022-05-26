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

    def testPassed(self, _description: str, _actual: str, _expected: str) -> None:
        self.gTestsPassed += 1

    def testFailed(self, _description: str, _actual: str, _expected: str) -> None:
        self.gTestsFailed += 1
        print(radd(")", radd(_expected, radd(" expected ", radd(_actual, radd(" (", radd(_description, "FAILED!: ")))))))
        self.builtin_funcs.llOwnerSay(typecast(rdiv(0, 0), str))

    def ensureTrue(self, _description: str, _actual: int) -> None:
        if cond(_actual):
            self.testPassed(_description, typecast(_actual, str), typecast(1, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(1, str))

    def ensureFalse(self, _description: str, _actual: int) -> None:
        if cond(_actual):
            self.testFailed(_description, typecast(_actual, str), typecast(0, str))
        else:
            self.testPassed(_description, typecast(_actual, str), typecast(0, str))

    def ensureIntegerEqual(self, _description: str, _actual: int, _expected: int) -> None:
        if cond(req(_expected, _actual)):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def floatEqual(self, _actual: float, _expected: float) -> int:
        _error: float = self.builtin_funcs.llFabs(rsub(_actual, _expected))
        _epsilon: float = bin2float('0.001000', '6f12833a')
        if cond(rgreater(_epsilon, _error)):
            self.builtin_funcs.llSay(0, radd(typecast(_error, str), "Float equality delta "))
            return 0
        return 1

    def ensureFloatEqual(self, _description: str, _actual: float, _expected: float) -> None:
        if cond(self.floatEqual(_actual, _expected)):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def ensureFloatExactEqual(self, _description: str, _actual: float, _expected: float) -> None:
        if cond(req(_expected, _actual)):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def ensureStringEqual(self, _description: str, _actual: str, _expected: str) -> None:
        if cond(req(_expected, _actual)):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def ensureKeyEqual(self, _description: str, _actual: Key, _expected: Key) -> None:
        if cond(req(_expected, _actual)):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def ensureVectorEqual(self, _description: str, _actual: Vector, _expected: Vector) -> None:
        if cond(rbooland(self.floatEqual(_actual[2], _expected[2]), rbooland(self.floatEqual(_actual[1], _expected[1]), self.floatEqual(_actual[0], _expected[0])))):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def ensureRotationEqual(self, _description: str, _actual: Quaternion, _expected: Quaternion) -> None:
        if cond(rbooland(self.floatEqual(_actual[3], _expected[3]), rbooland(self.floatEqual(_actual[2], _expected[2]), rbooland(self.floatEqual(_actual[1], _expected[1]), self.floatEqual(_actual[0], _expected[0]))))):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def ensureListEqual(self, _description: str, _actual: list, _expected: list) -> None:
        if cond(req(_expected, _actual)):
            self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    def testReturnFloat(self) -> float:
        return 1.0

    def testReturnKey(self) -> Key:
        return typecast("00000000-0000-0000-0000-000000000000", Key)

    def testArgumentAccessor(self, _v: Vector) -> None:
        _v = Vector((0.0, 0.0, 0.0))
        _v = replace_coord_axis(_v, 0, self.testReturnFloat())
        _v = replace_coord_axis(_v, 1, self.testReturnFloat())
        _v = replace_coord_axis(_v, 2, self.testReturnFloat())
        self.ensureVectorEqual("testArgumentAccessor", _v, Vector((1.0, 1.0, 1.0)))

    def testLocalAccessor(self) -> None:
        _v: Vector = Vector((0.0, 0.0, 0.0))
        _v = replace_coord_axis(_v, 0, self.testReturnFloat())
        _v = replace_coord_axis(_v, 1, self.testReturnFloat())
        _v = replace_coord_axis(_v, 2, self.testReturnFloat())
        self.ensureVectorEqual("testLocalAccessor", _v, Vector((1.0, 1.0, 1.0)))

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
        _k: Key = typecast("foo", Key)
        _k2: Key = typecast("foo", Key)
        self.ensureKeyEqual("k = \"foo\";k2 = \"foo\";k == k2", _k, _k2)
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
        _l: list = []
        _l = [42]
        radd(1, _l)
        self.ensureListEqual("list l = [42]; l + 1; l == [42]", _l, [42])
        _l = [42]
        radd(bin2float('1.500000', '0000c03f'), _l)
        self.ensureListEqual("list l = [42]; l + 1.5; l == [42]", _l, [42])
        _l = [42]
        radd("00000000-0000-0000-0000-000000000000", _l)
        self.ensureListEqual("list l = [42]; l + NULL_KEY; l == [42]", _l, [42])
        _l = [42]
        radd(Vector((1.0, 2.0, 3.0)), _l)
        self.ensureListEqual("list l = [42]; l + <1,2,3>; l == [42]", _l, [42])
        _l = [42]
        radd(Quaternion((1.0, 2.0, 3.0, 4.0)), _l)
        self.ensureListEqual("list l = [42]; l + <1,2,3>; l == [42]", _l, [42])
        if cond(_k):
            self.testFailed("if(k)", "TRUE", "FALSE")
        else:
            self.testPassed("if(k)", "FALSE", "FALSE")
        self.ensureIntegerEqual("k == \"foo\"", req("foo", _k), 1)
        self.ensureIntegerEqual("gStringInAKey == \"foo\"", req("foo", self.gStringInAKey), 1)
        self.ensureIntegerEqual("gNullKey == NULL_KEY", req("00000000-0000-0000-0000-000000000000", self.gNullKey), 1)
        _k = typecast("00000000-0000-0000-0000-000000000000", Key)
        _s: str = ""
        _s = typecast(_k, str)
        self.ensureStringEqual("k = NULL_KEY; string s; s = k;", _s, "00000000-0000-0000-0000-000000000000")
        _v: Vector = Vector((1.0, 1.0, 1.0))
        while cond(_v):
            _v = Vector((0.0, 0.0, 0.0))
        self.ensureVectorEqual("while (v) { v = ZERO_VECTOR; }", _v, Vector((0.0, 0.0, 0.0)))
        _v = Vector((2.0, 2.0, 2.0))
        while True == True:
            _v = Vector((0.0, 0.0, 0.0))
            if not cond(_v):
                break
        self.ensureVectorEqual("v = <2,2,2>; do { v = ZERO_VECTOR } while (v);", _v, Vector((0.0, 0.0, 0.0)))
        _v = Vector((3.0, 3.0, 3.0))
        while True == True:
            if not cond(_v):
                break
            pass
            _v = Vector((0.0, 0.0, 0.0))
        self.ensureVectorEqual("for (v = <3,3,3>;v;v=ZERO_VECTOR) {}", _v, Vector((0.0, 0.0, 0.0)))
        _k = typecast("7c42811e-229f-4500-b6d7-2c37324ff816", Key)
        while cond(_k):
            _k = typecast("00000000-0000-0000-0000-000000000000", Key)
        self.ensureKeyEqual("while (k) { k = NULL_KEY; }", _k, typecast("00000000-0000-0000-0000-000000000000", Key))
        _k = typecast("7c42811e-229f-4500-b6d7-2c37324ff816", Key)
        while True == True:
            _k = typecast("00000000-0000-0000-0000-000000000000", Key)
            if not cond(_k):
                break
        self.ensureKeyEqual("k = \"7c42811e-229f-4500-b6d7-2c37324ff816\"; do { k = NULL_KEY } while (k);", _k, typecast("00000000-0000-0000-0000-000000000000", Key))
        _k = typecast("7c42811e-229f-4500-b6d7-2c37324ff816", Key)
        while True == True:
            if not cond(_k):
                break
            pass
            _k = typecast("00000000-0000-0000-0000-000000000000", Key)
        self.ensureKeyEqual("for (k = \"7c42811e-229f-4500-b6d7-2c37324ff816\";k;k=NULL_KEY) {}", _k, typecast("00000000-0000-0000-0000-000000000000", Key))
        _q: Quaternion = Quaternion((1.0, 1.0, 1.0, 1.0))
        while cond(_q):
            _q = Quaternion((0.0, 0.0, 0.0, 1.0))
        self.ensureRotationEqual("while (q) { q = ZERO_ROTATION; }", _q, Quaternion((0.0, 0.0, 0.0, 1.0)))
        _q = Quaternion((2.0, 2.0, 2.0, 2.0))
        while True == True:
            _q = Quaternion((0.0, 0.0, 0.0, 1.0))
            if not cond(_q):
                break
        self.ensureRotationEqual("q = <2,2,2>; do { v = ZERO_ROTATION } while (q);", _q, Quaternion((0.0, 0.0, 0.0, 1.0)))
        _q = Quaternion((3.0, 3.0, 3.0, 3.0))
        while True == True:
            if not cond(_q):
                break
            pass
            _q = Quaternion((0.0, 0.0, 0.0, 1.0))
        self.ensureRotationEqual("for (q = <3,3,3,3>;q;q=ZERO_ROTATION) {}", _q, Quaternion((0.0, 0.0, 0.0, 1.0)))
        _l = [1]
        _l = [2]
        while True == True:
            _l = []
            if not cond(_l):
                break
        self.ensureListEqual("l = [2]; do { v = [] } while (l);", _l, [])
        _s = "1!"
        while cond(_s):
            _s = ""
        self.ensureStringEqual("while (s) { s = \"\"; }", _s, "")
        _s = "2!"
        while True == True:
            _s = ""
            if not cond(_s):
                break
        self.ensureStringEqual("s = \"2!\"; do { s = \"\" } while (s);", _s, "")
        _s = "3!"
        while True == True:
            if not cond(_s):
                break
            pass
            _s = ""
        self.ensureStringEqual("for (s = \"3!\";s;s=\"\") {}", _s, "")
        _i: int = 1
        while cond(_i):
            _i = 0
        self.ensureIntegerEqual("while (i) { i = 0; }", _i, 0)
        _i = 2
        while True == True:
            _i = 0
            if not cond(_i):
                break
        self.ensureIntegerEqual("i = 2; do { i = 0 } while (i);", _i, 0)
        _i = 3
        while True == True:
            if not cond(_i):
                break
            pass
            _i = 0
        self.ensureIntegerEqual("for (i = 3;i;i=0) {}", _i, 0)
        _f: float = 1.0
        while cond(_f):
            _f = 0.0
        self.ensureFloatEqual("while (f) { f = 0; }", _f, 0.0)
        _f = 2.0
        while True == True:
            _f = 0.0
            if not cond(_f):
                break
        self.ensureFloatEqual("f = 2; do { f = 0 } while (f);", _f, 0.0)
        _f = 3.0
        while True == True:
            if not cond(_f):
                break
            pass
            _f = 0.0
        self.ensureFloatEqual("for (f = 3;f;f=0) {}", _f, 0.0)
        _v = Vector((1.0, 2.0, 3.0))
        _v = rmul(2.0, _v)
        self.ensureVectorEqual("v = <1,2,3>; v *= 2;", _v, Vector((2.0, 4.0, 6.0)))
        _v = Vector((1.0, 2.0, 3.0))
        _v = rmul(bin2float('0.500000', '0000003f'), _v)
        self.ensureVectorEqual("v = <1,2,3>; v *= 0.5;", _v, Vector((bin2float('0.500000', '0000003f'), 1.0, bin2float('1.500000', '0000c03f'))))
        _v = Vector((1.0, 0.0, 0.0))
        _v = rmul(Quaternion((0.0, 0.0, 0.0, 1.0)), _v)
        self.ensureVectorEqual("vector v = <1,0,0>; v *= ZERO_ROTATION;", _v, Vector((1.0, 0.0, 0.0)))
        _v = Vector((0.0, 1.0, 0.0))
        _v = rmod(Vector((0.0, 0.0, 1.0)), _v)
        self.ensureVectorEqual("vector v = <0,1,0>; v %= <0,0,1>;", _v, Vector((1.0, 0.0, 0.0)))
        _r: Quaternion = Quaternion((0.0, 0.0, 0.0, 1.0))
        _r = rmul(Quaternion((0.0, 0.0, 0.0, 1.0)), _r)
        self.ensureRotationEqual("rotation r = ZERO_ROTATION; r *= ZERO_ROTATION;", _r, Quaternion((0.0, 0.0, 0.0, 1.0)))
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
        _defaultKey: Key = Key("")
        self.ensureKeyEqual("key defaultKey;", _defaultKey, typecast("", Key))
        _defaultInteger: int = 0
        self.ensureIntegerEqual("key defaultInteger;", _defaultInteger, 0)
        _defaultFloat: float = 0.0
        self.ensureFloatEqual("key defaultInteger;", _defaultFloat, 0.0)
        _defaultString: str = ""
        self.ensureStringEqual("string defaultString;", _defaultString, "")
        self.ensureIntegerEqual("chat == TRUE", self.chat, 1)

    def runTests(self) -> None:
        self.gTestsPassed = 0
        self.gTestsFailed = 0
        self.tests()
        self.gVisitedStateTest = 0
        print("Test succeeded")

    def edefaultstate_entry(self) -> None:
        raise StateChangeException('StateTest')

    def edefaulttouch_start(self, _total_number: int) -> None:
        raise StateChangeException('StateTest')

    def eStateTeststate_entry(self) -> None:
        self.ensureFalse("gVisitedStateTest", self.gVisitedStateTest)
        self.gVisitedStateTest = 1
        self.runTests()

    def eStateTesttouch_start(self, _total_number: int) -> None:
        raise StateChangeException('default')

