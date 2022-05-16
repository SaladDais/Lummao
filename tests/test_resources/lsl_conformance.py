from lummao import *


class Script(BaseLSLScript):
    gTestsPassed: int
    gTestsFailed: int
    gInteger: int
    gFloat: float
    gString: str
    gVector: Vector
    gRot: Quaternion
    gList: list
    gCallOrder: list

    def __init__(self):
        super().__init__()
        self.gTestsPassed = 0
        self.gTestsFailed = 0
        self.gInteger = 5
        self.gFloat = bin2float('1.500000', '0000c03f')
        self.gString = "foo"
        self.gVector = Vector((float(1), float(2), float(3)))
        self.gRot = Quaternion((float(1), float(2), float(3), float(4)))
        self.gList = [1, 2, 3]
        self.gCallOrder = []

    @with_goto
    def testPassed(self, description: str, actual: str, expected: str) -> None:
        self.gTestsPassed += 1

    @with_goto
    def testFailed(self, description: str, actual: str, expected: str) -> None:
        self.gTestsFailed += 1
        print(radd(")", radd(expected, radd(" expected ", radd(actual, radd(" (", radd(description, "FAILED!: ")))))))
        lslfuncs.llOwnerSay(typecast(rdiv(0, 0), str))

    @with_goto
    def ensureTrue(self, description: str, actual: int) -> None:
        if cond(actual):
            self.testPassed(description, typecast(actual, str), typecast(1, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(1, str))

    @with_goto
    def ensureFalse(self, description: str, actual: int) -> None:
        if cond(actual):
            self.testFailed(description, typecast(actual, str), typecast(0, str))
        else:
            self.testPassed(description, typecast(actual, str), typecast(0, str))

    @with_goto
    def ensureIntegerEqual(self, description: str, actual: int, expected: int) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    @with_goto
    def floatEqual(self, actual: float, expected: float) -> int:
        error: float = lslfuncs.llFabs(rsub(actual, expected))
        epsilon: float = bin2float('0.001000', '6f12833a')
        if cond(rgreater(epsilon, error)):
            print(radd(typecast(error, str), "Float equality delta "))
            return 0
        return 1

    @with_goto
    def ensureFloatEqual(self, description: str, actual: float, expected: float) -> None:
        if cond(self.floatEqual(actual, expected)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    @with_goto
    def ensureStringEqual(self, description: str, actual: str, expected: str) -> None:
        if cond(req(expected, actual)):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    @with_goto
    def ensureVectorEqual(self, description: str, actual: Vector, expected: Vector) -> None:
        if cond(rbooland(self.floatEqual(actual[2], expected[2]), rbooland(self.floatEqual(actual[1], expected[1]), self.floatEqual(actual[0], expected[0])))):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    @with_goto
    def ensureRotationEqual(self, description: str, actual: Quaternion, expected: Quaternion) -> None:
        if cond(rbooland(self.floatEqual(actual[3], expected[3]), rbooland(self.floatEqual(actual[2], expected[2]), rbooland(self.floatEqual(actual[1], expected[1]), self.floatEqual(actual[0], expected[0]))))):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    @with_goto
    def ensureListEqual(self, description: str, actual: list, expected: list) -> None:
        if cond(rbooland((req(typecast(expected, str), typecast(actual, str))), req(expected, actual))):
            self.testPassed(description, typecast(actual, str), typecast(expected, str))
        else:
            self.testFailed(description, typecast(actual, str), typecast(expected, str))

    @with_goto
    def callOrderFunc(self, num: int) -> int:
        self.gCallOrder = radd([num], self.gCallOrder)
        return 1

    @with_goto
    def testReturn(self) -> int:
        return 1

    @with_goto
    def testReturnFloat(self) -> float:
        return 1.0

    @with_goto
    def testReturnString(self) -> str:
        return "Test string"

    @with_goto
    def testReturnList(self) -> list:
        return [1, 2, 3]

    @with_goto
    def testReturnVector(self) -> Vector:
        return Vector((float(1), float(2), float(3)))

    @with_goto
    def testReturnRotation(self) -> Quaternion:
        return Quaternion((float(1), float(2), float(3), float(4)))

    @with_goto
    def testReturnVectorNested(self) -> Vector:
        return self.testReturnVector()

    @with_goto
    def testReturnVectorWithLibraryCall(self) -> Vector:
        lslfuncs.llSin(float(0))
        return Vector((float(1), float(2), float(3)))

    @with_goto
    def testReturnRotationWithLibraryCall(self) -> Quaternion:
        lslfuncs.llSin(float(0))
        return Quaternion((float(1), float(2), float(3), float(4)))

    @with_goto
    def testParameters(self, param: int) -> int:
        param = radd(1, param)
        return param

    @with_goto
    def testRecursion(self, param: int) -> int:
        if cond(rleq(0, param)):
            return 0
        else:
            return self.testRecursion(rsub(1, param))

    @with_goto
    def testExpressionLists(self, l: list) -> str:
        return radd(typecast(l, str), "foo")

    @with_goto
    def tests(self) -> None:
        self.ensureIntegerEqual("TRUE", 1, 1)
        self.ensureIntegerEqual("FALSE", 0, 0)
        if cond(0.0):
            self.testFailed("if(0.0)", "TRUE", "FALSE")
        else:
            self.testPassed("if(0.0)", "TRUE", "TRUE")
        if cond(bin2float('0.000001', 'bd378635')):
            self.testPassed("if(0.000001)", "TRUE", "TRUE")
        else:
            self.testFailed("if(0.000001)", "TRUE", "FALSE")
        if cond(bin2float('0.900000', '6666663f')):
            self.testPassed("if(0.9)", "TRUE", "TRUE")
        else:
            self.testFailed("if(0.9)", "TRUE", "FALSE")
        if cond(Vector((0.0, 0.0, 0.0))):
            self.testFailed("if(ZERO_VECTOR)", "TRUE", "FALSE")
        else:
            self.testPassed("if(ZERO_VECTOR)", "TRUE", "TRUE")
        if cond(Quaternion((0.0, 0.0, 0.0, 1.0))):
            self.testFailed("if(ZERO_ROTATION)", "TRUE", "FALSE")
        else:
            self.testPassed("if(ZERO_ROTATION)", "TRUE", "TRUE")
        if cond("00000000-0000-0000-0000-000000000000"):
            self.testPassed("if(NULL_KEY)", "TRUE", "TRUE")
        else:
            self.testFailed("if(NULL_KEY)", "TRUE", "FALSE")
        if cond(typecast("00000000-0000-0000-0000-000000000000", Key)):
            self.testFailed("if((key)NULL_KEY)", "TRUE", "FALSE")
        else:
            self.testPassed("if((key)NULL_KEY)", "TRUE", "TRUE")
        if cond(""):
            self.testFailed("if(\"\")", "TRUE", "FALSE")
        else:
            self.testPassed("if(\"\")", "TRUE", "TRUE")
        if cond([]):
            self.testFailed("if([])", "TRUE", "FALSE")
        else:
            self.testPassed("if([])", "TRUE", "TRUE")
        self.ensureIntegerEqual("(TRUE == TRUE)", (req(1, 1)), 1)
        self.ensureIntegerEqual("(TRUE == FALSE)", (req(0, 1)), 0)
        self.ensureIntegerEqual("(FALSE == TRUE)", (req(1, 0)), 0)
        self.ensureIntegerEqual("(FALSE == FALSE)", (req(0, 0)), 1)
        self.ensureIntegerEqual("(TRUE != TRUE)", (rneq(1, 1)), 0)
        self.ensureIntegerEqual("(TRUE != FALSE)", (rneq(0, 1)), 1)
        self.ensureIntegerEqual("(FALSE != TRUE)", (rneq(1, 0)), 1)
        self.ensureIntegerEqual("(FALSE != FALSE)", (rneq(0, 0)), 0)
        self.ensureIntegerEqual("(TRUE && TRUE)", (rbooland(1, 1)), 1)
        self.ensureIntegerEqual("(TRUE && FALSE)", (rbooland(0, 1)), 0)
        self.ensureIntegerEqual("(FALSE && TRUE)", (rbooland(1, 0)), 0)
        self.ensureIntegerEqual("(FALSE && FALSE)", (rbooland(0, 0)), 0)
        self.ensureIntegerEqual("(1 && 2)", (rbooland(2, 1)), 1)
        self.ensureIntegerEqual("(1 && 0)", (rbooland(0, 1)), 0)
        self.ensureIntegerEqual("(0 && 2)", (rbooland(2, 0)), 0)
        self.ensureIntegerEqual("(0 && 0)", (rbooland(0, 0)), 0)
        self.ensureIntegerEqual("(TRUE || TRUE)", (rboolor(1, 1)), 1)
        self.ensureIntegerEqual("(TRUE || FALSE)", (rboolor(0, 1)), 1)
        self.ensureIntegerEqual("(FALSE || TRUE)", (rboolor(1, 0)), 1)
        self.ensureIntegerEqual("(FALSE || FALSE)", (rboolor(0, 0)), 0)
        self.ensureIntegerEqual("(1 || 2)", (rboolor(2, 1)), 1)
        self.ensureIntegerEqual("(1 || 0)", (rboolor(0, 1)), 1)
        self.ensureIntegerEqual("(0 || 2)", (rboolor(2, 0)), 1)
        self.ensureIntegerEqual("(0 || 0)", (rboolor(0, 0)), 0)
        self.ensureIntegerEqual("(! TRUE)", (boolnot(1)), 0)
        self.ensureIntegerEqual("(! FALSE)", (boolnot(0)), 1)
        self.ensureIntegerEqual("(! 2)", (boolnot(2)), 0)
        self.ensureIntegerEqual("(! 0)", (boolnot(0)), 1)
        self.ensureIntegerEqual("(1 > 0)", (rgreater(0, 1)), 1)
        self.ensureIntegerEqual("(0 > 1)", (rgreater(1, 0)), 0)
        self.ensureIntegerEqual("(1 > 1)", (rgreater(1, 1)), 0)
        self.ensureIntegerEqual("(0 < 1)", (rless(1, 0)), 1)
        self.ensureIntegerEqual("(1 < 0)", (rless(0, 1)), 0)
        self.ensureIntegerEqual("(1 < 1)", (rless(1, 1)), 0)
        self.ensureIntegerEqual("(1 >= 0)", (rgeq(0, 1)), 1)
        self.ensureIntegerEqual("(0 >= 1)", (rgeq(1, 0)), 0)
        self.ensureIntegerEqual("(1 >= 1)", (rgeq(1, 1)), 1)
        self.ensureIntegerEqual("(0 <= 1)", (rleq(1, 0)), 1)
        self.ensureIntegerEqual("(1 <= 0)", (rleq(0, 1)), 0)
        self.ensureIntegerEqual("(1 <= 1)", (rleq(1, 1)), 1)
        self.ensureIntegerEqual("(10 & 25)", (rbitand(25, 10)), 8)
        self.ensureIntegerEqual("(10 | 25)", (rbitor(25, 10)), 27)
        self.ensureIntegerEqual("~10", bitnot(10), -11)
        self.ensureIntegerEqual("(10 ^ 25)", (rbitxor(25, 10)), 19)
        self.ensureIntegerEqual("(523 >> 2)", (rshr(2, 523)), 130)
        self.ensureIntegerEqual("(523 << 2)", (rshl(2, 523)), 2092)
        self.ensureIntegerEqual("(1 + 1)", (radd(1, 1)), 2)
        self.ensureFloatEqual("(1 + 1.1)", (radd(bin2float('1.100000', 'cdcc8c3f'), float(1))), bin2float('2.100000', '66660640'))
        self.ensureFloatEqual("(1.1 + 1)", (radd(float(1), bin2float('1.100000', 'cdcc8c3f'))), bin2float('2.100000', '66660640'))
        self.ensureFloatEqual("(1.1 + 1.1)", (radd(bin2float('1.100000', 'cdcc8c3f'), bin2float('1.100000', 'cdcc8c3f'))), bin2float('2.200000', 'cdcc0c40'))
        self.ensureStringEqual("\"foo\" + \"bar\"", radd("bar", "foo"), "foobar")
        self.ensureVectorEqual("(<1.1, 2.2, 3.3> + <4.4, 5.5, 6.6>)", (radd(Vector((bin2float('4.400000', 'cdcc8c40'), bin2float('5.500000', '0000b040'), bin2float('6.600000', '3333d340'))), Vector((bin2float('1.100000', 'cdcc8c3f'), bin2float('2.200000', 'cdcc0c40'), bin2float('3.300000', '33335340'))))), Vector((bin2float('5.500000', '0000b040'), bin2float('7.700000', '6666f640'), bin2float('9.900000', '66661e41'))))
        self.ensureRotationEqual("(<1.1, 2.2, 3.3, 4.4> + <4.4, 5.5, 6.6, 3.3>)", (radd(Quaternion((bin2float('4.400000', 'cdcc8c40'), bin2float('5.500000', '0000b040'), bin2float('6.600000', '3333d340'), bin2float('3.300000', '33335340'))), Quaternion((bin2float('1.100000', 'cdcc8c3f'), bin2float('2.200000', 'cdcc0c40'), bin2float('3.300000', '33335340'), bin2float('4.400000', 'cdcc8c40'))))), Quaternion((bin2float('5.500000', '0000b040'), bin2float('7.700000', '6666f640'), bin2float('9.900000', '66661e41'), bin2float('7.700000', '6666f640'))))
        self.ensureListEqual("([1] + 2)", (radd(2, [1])), [1, 2])
        self.ensureListEqual("([] + 1.5)", (radd(bin2float('1.500000', '0000c03f'), [])), [bin2float('1.500000', '0000c03f')])
        self.ensureListEqual("([\"foo\"] + \"bar\")", (radd("bar", ["foo"])), ["foo", "bar"])
        self.ensureListEqual("([] + <1,2,3>)", (radd(Vector((float(1), float(2), float(3))), [])), [Vector((float(1), float(2), float(3)))])
        self.ensureListEqual("([] + <1,2,3,4>)", (radd(Quaternion((float(1), float(2), float(3), float(4))), [])), [Quaternion((float(1), float(2), float(3), float(4)))])
        self.ensureListEqual("(1 + [2])", (radd([2], 1)), [1, 2])
        self.ensureListEqual("(1.0 + [2])", (radd([2], 1.0)), [1.0, 2])
        self.ensureListEqual("(1 + [2])", (radd([2], "one")), ["one", 2])
        self.ensureListEqual("(<1.0,1.0,1.0,1.0> + [2])", (radd([2], Quaternion((1.0, 1.0, 1.0, 1.0)))), [Quaternion((1.0, 1.0, 1.0, 1.0)), 2])
        self.ensureListEqual("(<1.0,1.0,1.0> + [2])", (radd([2], Vector((1.0, 1.0, 1.0)))), [Vector((1.0, 1.0, 1.0)), 2])
        a: list = []
        b: list = a
        a = radd(["foo"], a)
        self.ensureListEqual("list a = []; list b = a; a += [\"foo\"]; a == [\"foo\"]", a, ["foo"])
        self.ensureListEqual("list a = []; list b = a; a += [\"foo\"]; b == []", b, [])
        a = ["a"]
        b = ["b"]
        c: list = radd(b, a)
        self.ensureListEqual("a = [\"a\"]; b = [\"b\"]; list c = a + b; a == [\"a\"];", a, ["a"])
        self.ensureListEqual("a = [\"a\"]; b = [\"b\"]; list c = a + b; b == [\"b\"];", b, ["b"])
        self.ensureListEqual("a = [\"a\"]; b = [\"b\"]; list c = a + b; c == [\"a\", \"b\"];", c, ["a", "b"])
        self.ensureIntegerEqual("(1 - 1)", (rsub(1, 1)), 0)
        self.ensureFloatEqual("(1 - 0.5)", (rsub(bin2float('0.500000', '0000003f'), float(1))), bin2float('0.500000', '0000003f'))
        self.ensureFloatEqual("(1.5 - 1)", (rsub(float(1), bin2float('1.500000', '0000c03f'))), bin2float('0.500000', '0000003f'))
        self.ensureFloatEqual("(2.2 - 1.1)", (rsub(bin2float('1.100000', 'cdcc8c3f'), bin2float('2.200000', 'cdcc0c40'))), bin2float('1.100000', 'cdcc8c3f'))
        self.ensureVectorEqual("(<1.5, 2.5, 3.5> - <4.5, 5.5, 6.5>)", (rsub(Vector((bin2float('4.500000', '00009040'), bin2float('5.500000', '0000b040'), bin2float('6.500000', '0000d040'))), Vector((bin2float('1.500000', '0000c03f'), bin2float('2.500000', '00002040'), bin2float('3.500000', '00006040'))))), Vector((-3.0, -3.0, -3.0)))
        self.ensureRotationEqual("(<1.5, 2.5, 3.5, 4.5> - <4.5, 5.5, 6.5, 7.5>)", (rsub(Quaternion((bin2float('4.500000', '00009040'), bin2float('5.500000', '0000b040'), bin2float('6.500000', '0000d040'), bin2float('7.500000', '0000f040'))), Quaternion((bin2float('1.500000', '0000c03f'), bin2float('2.500000', '00002040'), bin2float('3.500000', '00006040'), bin2float('4.500000', '00009040'))))), Quaternion((-3.0, -3.0, -3.0, -3.0)))
        self.ensureIntegerEqual("(2 * 3)", (rmul(3, 2)), 6)
        self.ensureFloatEqual("(2 * 3.5)", (rmul(bin2float('3.500000', '00006040'), float(2))), 7.0)
        self.ensureFloatEqual("(2.5 * 3)", (rmul(float(3), bin2float('2.500000', '00002040'))), bin2float('7.500000', '0000f040'))
        self.ensureFloatEqual("(2.5 * 3.5)", (rmul(bin2float('3.500000', '00006040'), bin2float('2.500000', '00002040'))), bin2float('8.750000', '00000c41'))
        self.ensureVectorEqual("(<1.1, 2.2, 3.3> * 2)", (rmul(float(2), Vector((bin2float('1.100000', 'cdcc8c3f'), bin2float('2.200000', 'cdcc0c40'), bin2float('3.300000', '33335340'))))), Vector((bin2float('2.200000', 'cdcc0c40'), bin2float('4.400000', 'cdcc8c40'), bin2float('6.600000', '3333d340'))))
        self.ensureVectorEqual("(2 * <1.1, 2.2, 3.3>)", (rmul(float(2), Vector((bin2float('1.100000', 'cdcc8c3f'), bin2float('2.200000', 'cdcc0c40'), bin2float('3.300000', '33335340'))))), (rmul(Vector((bin2float('1.100000', 'cdcc8c3f'), bin2float('2.200000', 'cdcc0c40'), bin2float('3.300000', '33335340'))), float(2))))
        self.ensureVectorEqual("(<2.2, 4.4, 6.6> * 2.0)", (rmul(2.0, Vector((bin2float('2.200000', 'cdcc0c40'), bin2float('4.400000', 'cdcc8c40'), bin2float('6.600000', '3333d340'))))), Vector((bin2float('4.400000', 'cdcc8c40'), bin2float('8.800000', 'cdcc0c41'), bin2float('13.200000', '33335341'))))
        self.ensureVectorEqual("(2.0 * <2.2, 4.4, 6.6>)", (rmul(2.0, Vector((bin2float('2.200000', 'cdcc0c40'), bin2float('4.400000', 'cdcc8c40'), bin2float('6.600000', '3333d340'))))), (rmul(Vector((bin2float('2.200000', 'cdcc0c40'), bin2float('4.400000', 'cdcc8c40'), bin2float('6.600000', '3333d340'))), 2.0)))
        self.ensureFloatEqual("<1,3,-5> * <4,-2,-1>", rmul(Vector((float(4), float(-2), float(-1))), Vector((float(1), float(3), float(-5)))), 3.0)
        self.ensureVectorEqual("<-1,0,0> * <0, 0, 0.707, 0.707>", rmul(Quaternion((float(0), float(0), bin2float('0.707000', 'f4fd343f'), bin2float('0.707000', 'f4fd343f'))), Vector((float(-1), float(0), float(0)))), Vector((float(0), float(-1), float(0))))
        self.ensureRotationEqual("(<1.0, 2.0, 3.0, 4.0> * <5.0, 6.0, 7.0, 8.0>)", (rmul(Quaternion((5.0, 6.0, 7.0, 8.0)), Quaternion((1.0, 2.0, 3.0, 4.0)))), Quaternion((32.0, 32.0, 56.0, -6.0)))
        self.ensureIntegerEqual("(2 / 2)", (rdiv(2, 2)), 1)
        self.ensureFloatEqual("(2.2 / 2)", (rdiv(float(2), bin2float('2.200000', 'cdcc0c40'))), bin2float('1.100000', 'cdcc8c3f'))
        self.ensureFloatEqual("(3 / 1.5)", (rdiv(bin2float('1.500000', '0000c03f'), float(3))), 2.0)
        self.ensureFloatEqual("(2.2 / 2.0)", (rdiv(2.0, bin2float('2.200000', 'cdcc0c40'))), bin2float('1.100000', 'cdcc8c3f'))
        self.ensureVectorEqual("(<1.0, 2.0, 3.0> / 2)", (rdiv(float(2), Vector((1.0, 2.0, 3.0)))), Vector((bin2float('0.500000', '0000003f'), 1.0, bin2float('1.500000', '0000c03f'))))
        self.ensureVectorEqual("(<3.0, 6.0, 9.0> / 1.5)", (rdiv(bin2float('1.500000', '0000c03f'), Vector((3.0, 6.0, 9.0)))), Vector((2.0, 4.0, 6.0)))
        self.ensureVectorEqual("<-1,0,0> / <0, 0, 0.707, 0.707>", rdiv(Quaternion((float(0), float(0), bin2float('0.707000', 'f4fd343f'), bin2float('0.707000', 'f4fd343f'))), Vector((float(-1), float(0), float(0)))), Vector((float(0), float(1), float(0))))
        self.ensureRotationEqual("(<1.0, 2.0, 3.0, 4.0> / <5.0, 6.0, 7.0, 8.0>)", (rdiv(Quaternion((5.0, 6.0, 7.0, 8.0)), Quaternion((1.0, 2.0, 3.0, 4.0)))), Quaternion((-16.0, 0.0, -8.0, 70.0)))
        self.ensureIntegerEqual("(3 % 1)", (rmod(1, 3)), 0)
        self.ensureVectorEqual("(<1.0, 2.0, 3.0> % <4.0, 5.0, 6.0>)", (rmod(Vector((4.0, 5.0, 6.0)), Vector((1.0, 2.0, 3.0)))), Vector((-3.0, 6.0, -3.0)))
        i: int = 1
        self.ensureIntegerEqual("i = 1;", i, 1)
        i = 1
        i = radd(1, i)
        self.ensureIntegerEqual("i = 1; i += 1;", i, 2)
        i = 1
        i = rsub(1, i)
        self.ensureIntegerEqual("i = 1; i -= 1;", i, 0)
        i = 2
        i = rmul(2, i)
        self.ensureIntegerEqual("i = 2; i *= 2;", i, 4)
        i = 1
        (i := typecast(rmul(bin2float('0.500000', '0000003f'), i), int))
        self.ensureIntegerEqual("i = 1; i *= 0.5;", i, 0)
        i = 2
        i = rdiv(2, i)
        self.ensureIntegerEqual("i = 2; i /= 2;", i, 1)
        i = rdiv(-1, -2147483648)
        self.ensureIntegerEqual("i = 0x80000000 / -1;", i, -2147483648)
        i = 3
        i = rmod(1, i)
        self.ensureIntegerEqual("i = 3; i %= 1;", i, 0)
        i = rmod(-1, -2147483648)
        self.ensureIntegerEqual("i = 0x80000000 % -1;", i, 0)
        i = 1
        self.ensureIntegerEqual("postinc", rbooland((req(1, postincr(locals(), "i"))), (req(2, i))), 1)
        i = 1
        self.ensureIntegerEqual("preinc", rbooland((req(2, preincr(locals(), "i"))), (req(2, i))), 1)
        i = 2
        self.ensureIntegerEqual("postdec", rbooland((req(2, postdecr(locals(), "i"))), (req(1, i))), 1)
        i = 2
        self.ensureIntegerEqual("predec1", rbooland((req(1, predecr(locals(), "i"))), (req(1, i))), 1)
        i = 2
        i -= 1
        self.ensureIntegerEqual("predec2", i, 1)
        self.ensureFloatEqual("((float)2)", (float(2)), 2.0)
        self.ensureStringEqual("((string)2)", (typecast(2, str)), "2")
        self.ensureIntegerEqual("((integer) 1.5)", (typecast(bin2float('1.500000', '0000c03f'), int)), 1)
        self.ensureStringEqual("((string) 1.5)", (typecast(bin2float('1.500000', '0000c03f'), str)), "1.500000")
        self.ensureIntegerEqual("((integer) \"0xF\")", (typecast("0xF", int)), 15)
        self.ensureIntegerEqual("((integer) \"2\")", (typecast("2", int)), 2)
        self.ensureFloatEqual("((float) \"1.5\")", (typecast("1.5", float)), bin2float('1.500000', '0000c03f'))
        self.ensureVectorEqual("((vector) \"<1,2,3>\")", (typecast("<1,2,3>", Vector)), Vector((float(1), float(2), float(3))))
        self.ensureRotationEqual("((quaternion) \"<1,2,3,4>\")", (typecast("<1,2,3,4>", Quaternion)), Quaternion((float(1), float(2), float(3), float(4))))
        self.ensureStringEqual("((string) <1,2,3>)", (typecast(Vector((float(1), float(2), float(3))), str)), "<1.00000, 2.00000, 3.00000>")
        self.ensureStringEqual("((string) <1,2,3,4>)", (typecast(Quaternion((float(1), float(2), float(3), float(4))), str)), "<1.00000, 2.00000, 3.00000, 4.00000>")
        self.ensureStringEqual("((string) [1,2.5,<1,2,3>])", (typecast([1, bin2float('2.500000', '00002040'), Vector((float(1), float(2), float(3)))], str)), "12.500000<1.000000, 2.000000, 3.000000>")
        i = 0
        while cond(rless(10, i)):
            i += 1
        self.ensureIntegerEqual("i = 0; while(i < 10) ++i", i, 10)
        i = 0
        while True:
            i += 1
            if not cond(rless(10, i)):
                break
        self.ensureIntegerEqual("i = 0; do {++i;} while(i < 10);", i, 10)
        i = 0
        while True:
            if not cond(rless(10, i)):
                break
            pass
            i += 1
        self.ensureIntegerEqual("for(i = 0; i < 10; ++i);", i, 10)
        i = 1
        goto .SkipAssign
        lslfuncs.llSetText("Error", Vector((float(1), float(0), float(0))), float(1))
        i = 2
        label .SkipAssign
        self.ensureIntegerEqual("assignjump", i, 1)
        self.ensureIntegerEqual("testReturn()", self.testReturn(), 1)
        self.ensureFloatEqual("testReturnFloat()", self.testReturnFloat(), 1.0)
        self.ensureStringEqual("testReturnString()", self.testReturnString(), "Test string")
        self.ensureVectorEqual("testReturnVector()", self.testReturnVector(), Vector((float(1), float(2), float(3))))
        self.ensureRotationEqual("testReturnRotation()", self.testReturnRotation(), Quaternion((float(1), float(2), float(3), float(4))))
        self.ensureListEqual("testReturnList()", self.testReturnList(), [1, 2, 3])
        self.ensureVectorEqual("testReturnVectorNested()", self.testReturnVectorNested(), Vector((float(1), float(2), float(3))))
        self.ensureVectorEqual("libveccall", self.testReturnVectorWithLibraryCall(), Vector((float(1), float(2), float(3))))
        self.ensureRotationEqual("librotcall", self.testReturnRotationWithLibraryCall(), Quaternion((float(1), float(2), float(3), float(4))))
        self.ensureIntegerEqual("testParameters(1)", self.testParameters(1), 2)
        i = 1
        self.ensureIntegerEqual("i = 1; testParameters(i)", self.testParameters(i), 2)
        self.ensureIntegerEqual("testRecursion(10)", self.testRecursion(10), 0)
        self.ensureIntegerEqual("gInteger", self.gInteger, 5)
        self.ensureFloatEqual("gFloat", self.gFloat, bin2float('1.500000', '0000c03f'))
        self.ensureStringEqual("gString", self.gString, "foo")
        self.ensureVectorEqual("gVector", self.gVector, Vector((float(1), float(2), float(3))))
        self.ensureRotationEqual("gRot", self.gRot, Quaternion((float(1), float(2), float(3), float(4))))
        self.ensureListEqual("gList", self.gList, [1, 2, 3])
        self.gInteger = 1
        self.ensureIntegerEqual("gInteger = 1", self.gInteger, 1)
        self.gFloat = bin2float('0.500000', '0000003f')
        self.ensureFloatEqual("gFloat = 0.5", self.gFloat, bin2float('0.500000', '0000003f'))
        self.gString = "bar"
        self.ensureStringEqual("gString = \"bar\"", self.gString, "bar")
        self.gVector = Vector((float(3), float(3), float(3)))
        self.ensureVectorEqual("gVector = <3,3,3>", self.gVector, Vector((float(3), float(3), float(3))))
        self.gRot = Quaternion((float(3), float(3), float(3), float(3)))
        self.ensureRotationEqual("gRot = <3,3,3,3>", self.gRot, Quaternion((float(3), float(3), float(3), float(3))))
        self.gList = [4, 5, 6]
        self.ensureListEqual("gList = [4,5,6]", self.gList, [4, 5, 6])
        self.gVector = Vector((float(3), float(3), float(3)))
        self.ensureVectorEqual("-gVector = <-3,-3,-3>", neg(self.gVector), Vector((float(-3), float(-3), float(-3))))
        self.gRot = Quaternion((float(3), float(3), float(3), float(3)))
        self.ensureRotationEqual("-gRot = <-3,-3,-3,-3>", neg(self.gRot), Quaternion((float(-3), float(-3), float(-3), float(-3))))
        v: Vector = Vector((0.0, 0.0, 0.0))
        v = replace_coord_axis(v, 0, float(3))
        self.ensureFloatEqual("v.x", v[0], float(3))
        q: Quaternion = Quaternion((0.0, 0.0, 0.0, 1.0))
        q = replace_coord_axis(q, 3, float(5))
        self.ensureFloatEqual("q.s", q[3], float(5))
        self.gVector = replace_coord_axis(self.gVector, 1, bin2float('17.500000', '00008c41'))
        self.ensureFloatEqual("gVector.y = 17.5", self.gVector[1], bin2float('17.500000', '00008c41'))
        self.gRot = replace_coord_axis(self.gRot, 2, bin2float('19.500000', '00009c41'))
        self.ensureFloatEqual("gRot.z = 19.5", self.gRot[2], bin2float('19.500000', '00009c41'))
        l: list = typecast(5, list)
        l2: list = typecast(5, list)
        self.ensureListEqual("leq1", l, l2)
        self.ensureListEqual("leq2", l, [5])
        self.ensureListEqual("leq3", [bin2float('1.500000', '0000c03f'), 6, Vector((float(1), float(2), float(3))), Quaternion((float(1), float(2), float(3), float(4)))], [bin2float('1.500000', '0000c03f'), 6, Vector((float(1), float(2), float(3))), Quaternion((float(1), float(2), float(3), float(4)))])
        self.ensureIntegerEqual("sesc1", lslfuncs.llStringLength("\\"), 1)
        self.ensureIntegerEqual("sesc2", lslfuncs.llStringLength("    "), 4)
        self.ensureIntegerEqual("sesc3", lslfuncs.llStringLength("\n"), 1)
        self.ensureIntegerEqual("sesc4", lslfuncs.llStringLength("\""), 1)
        self.ensureStringEqual("testExpressionLists([testExpressionLists([]), \"bar\"]) == \"foofoobar\"", self.testExpressionLists([self.testExpressionLists([]), "bar"]), "foofoobar")
        if cond(rboolor(1, rbooland(rbitor(rbitxor(rdiv(self.callOrderFunc(5), self.callOrderFunc(4)), self.callOrderFunc(3)), self.callOrderFunc(2)), rboolor(rmul(self.callOrderFunc(1), self.callOrderFunc(0)), 1)))):
            pass
        self.ensureListEqual("gCallOrder expected order", self.gCallOrder, [5, 4, 3, 2, 1, 0])
        self.ensureIntegerEqual("(gInteger = 5)", (assign(self.__dict__, "gInteger", 5)), 5)
        self.ensureFloatEqual("(gVector.z = 6)", (assign(self.__dict__, "gVector", replace_coord_axis(self.gVector, 2, float(6)))[2]), float(6))
        self.gVector = Vector((float(1), float(2), float(3)))
        self.ensureFloatEqual("++gVector.z", preincr(self.__dict__, "gVector", 2), float(4))
        self.gVector = Vector((float(1), float(2), float(3)))
        self.ensureFloatEqual("gVector.z++", postincr(self.__dict__, "gVector", 2), float(3))
        self.ensureFloatEqual("(v.z = 6)", ((v := replace_coord_axis(v, 2, float(6)))[2]), float(6))
        v = Vector((float(1), float(2), float(3)))
        self.ensureFloatEqual("++v.z", preincr(locals(), "v", 2), float(4))
        v = Vector((float(1), float(2), float(3)))
        self.ensureFloatEqual("v.z++", postincr(locals(), "v", 2), float(3))

    @with_goto
    def runTests(self) -> None:
        self.gInteger = 5
        self.gFloat = bin2float('1.500000', '0000c03f')
        self.gString = "foo"
        self.gVector = Vector((float(1), float(2), float(3)))
        self.gRot = Quaternion((float(1), float(2), float(3), float(4)))
        self.gList = [1, 2, 3]
        self.gTestsPassed = 0
        self.gTestsFailed = 0
        self.gCallOrder = []
        self.tests()
        print("All tests passed")

    @with_goto
    def edefaultstate_entry(self) -> None:
        self.runTests()

