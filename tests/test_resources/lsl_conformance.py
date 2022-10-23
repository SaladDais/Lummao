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
        self.gFloat = 1.5
        self.gString = "foo"
        self.gVector = Vector((1.0, 2.0, 3.0))
        self.gRot = Quaternion((1.0, 2.0, 3.0, 4.0))
        self.gList = [1, 2, 3]
        self.gCallOrder = []

    async def testPassed(self, _description: str, _actual: str, _expected: str) -> None:
        self.gTestsPassed += 1

    async def testFailed(self, _description: str, _actual: str, _expected: str) -> None:
        self.gTestsFailed += 1
        print(radd(")", radd(_expected, radd(" expected ", radd(_actual, radd(" (", radd(_description, "FAILED!: ")))))))
        await self.builtin_funcs.llOwnerSay(typecast(rdiv(0, 0), str))

    async def ensureTrue(self, _description: str, _actual: int) -> None:
        if cond(_actual):
            await self.testPassed(_description, typecast(_actual, str), typecast(1, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(1, str))

    async def ensureFalse(self, _description: str, _actual: int) -> None:
        if cond(_actual):
            await self.testFailed(_description, typecast(_actual, str), typecast(0, str))
        else:
            await self.testPassed(_description, typecast(_actual, str), typecast(0, str))

    async def ensureIntegerEqual(self, _description: str, _actual: int, _expected: int) -> None:
        if cond(req(_expected, _actual)):
            await self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    async def floatEqual(self, _actual: float, _expected: float) -> int:
        _error: float = await self.builtin_funcs.llFabs(rsub(_actual, _expected))
        _epsilon: float = 0.001
        if cond(rgreater(_epsilon, _error)):
            print(radd(typecast(_error, str), "Float equality delta "))
            return 0
        return 1

    async def ensureFloatEqual(self, _description: str, _actual: float, _expected: float) -> None:
        if cond(await self.floatEqual(_actual, _expected)):
            await self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    async def ensureStringEqual(self, _description: str, _actual: str, _expected: str) -> None:
        if cond(req(_expected, _actual)):
            await self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    async def ensureVectorEqual(self, _description: str, _actual: Vector, _expected: Vector) -> None:
        if cond(rbooland(await self.floatEqual(_actual[2], _expected[2]), rbooland(await self.floatEqual(_actual[1], _expected[1]), await self.floatEqual(_actual[0], _expected[0])))):
            await self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    async def ensureRotationEqual(self, _description: str, _actual: Quaternion, _expected: Quaternion) -> None:
        if cond(rbooland(await self.floatEqual(_actual[3], _expected[3]), rbooland(await self.floatEqual(_actual[2], _expected[2]), rbooland(await self.floatEqual(_actual[1], _expected[1]), await self.floatEqual(_actual[0], _expected[0]))))):
            await self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    async def ensureListEqual(self, _description: str, _actual: list, _expected: list) -> None:
        if cond(rbooland((req(typecast(_expected, str), typecast(_actual, str))), req(_expected, _actual))):
            await self.testPassed(_description, typecast(_actual, str), typecast(_expected, str))
        else:
            await self.testFailed(_description, typecast(_actual, str), typecast(_expected, str))

    async def callOrderFunc(self, _num: int) -> int:
        self.gCallOrder = radd([_num], self.gCallOrder)
        return 1

    async def testReturn(self) -> int:
        return 1

    async def testReturnFloat(self) -> float:
        return 1.0

    async def testReturnString(self) -> str:
        return "Test string"

    async def testReturnList(self) -> list:
        return [1, 2, 3]

    async def testReturnVector(self) -> Vector:
        return Vector((1.0, 2.0, 3.0))

    async def testReturnRotation(self) -> Quaternion:
        return Quaternion((1.0, 2.0, 3.0, 4.0))

    async def testReturnVectorNested(self) -> Vector:
        return await self.testReturnVector()

    async def testReturnVectorWithLibraryCall(self) -> Vector:
        await self.builtin_funcs.llSin(0.0)
        return Vector((1.0, 2.0, 3.0))

    async def testReturnRotationWithLibraryCall(self) -> Quaternion:
        await self.builtin_funcs.llSin(0.0)
        return Quaternion((1.0, 2.0, 3.0, 4.0))

    async def testParameters(self, _param: int) -> int:
        _param = radd(1, _param)
        return _param

    async def testRecursion(self, _param: int) -> int:
        if cond(rleq(0, _param)):
            return 0
        else:
            return await self.testRecursion(rsub(1, _param))

    async def testExpressionLists(self, _l: list) -> str:
        return radd(typecast(_l, str), "foo")

    @with_goto
    async def tests(self) -> None:
        _a: Optional[list] = None
        _b: Optional[list] = None
        _c: Optional[list] = None
        _i: int = 0
        _v: Vector = Vector((0.0, 0.0, 0.0))
        _q: Quaternion = Quaternion((0.0, 0.0, 0.0, 0.0))
        _l: Optional[list] = None
        _l2: Optional[list] = None
        await self.ensureIntegerEqual("TRUE", 1, 1)
        await self.ensureIntegerEqual("FALSE", 0, 0)
        if cond(0.0):
            await self.testFailed("if(0.0)", "TRUE", "FALSE")
        else:
            await self.testPassed("if(0.0)", "TRUE", "TRUE")
        if cond(0.000001):
            await self.testPassed("if(0.000001)", "TRUE", "TRUE")
        else:
            await self.testFailed("if(0.000001)", "TRUE", "FALSE")
        if cond(0.9):
            await self.testPassed("if(0.9)", "TRUE", "TRUE")
        else:
            await self.testFailed("if(0.9)", "TRUE", "FALSE")
        if cond(Vector((0.0, 0.0, 0.0))):
            await self.testFailed("if(ZERO_VECTOR)", "TRUE", "FALSE")
        else:
            await self.testPassed("if(ZERO_VECTOR)", "TRUE", "TRUE")
        if cond(Quaternion((0.0, 0.0, 0.0, 1.0))):
            await self.testFailed("if(ZERO_ROTATION)", "TRUE", "FALSE")
        else:
            await self.testPassed("if(ZERO_ROTATION)", "TRUE", "TRUE")
        if cond("00000000-0000-0000-0000-000000000000"):
            await self.testPassed("if(NULL_KEY)", "TRUE", "TRUE")
        else:
            await self.testFailed("if(NULL_KEY)", "TRUE", "FALSE")
        if cond(typecast("00000000-0000-0000-0000-000000000000", Key)):
            await self.testFailed("if((key)NULL_KEY)", "TRUE", "FALSE")
        else:
            await self.testPassed("if((key)NULL_KEY)", "TRUE", "TRUE")
        if cond(""):
            await self.testFailed("if(\"\")", "TRUE", "FALSE")
        else:
            await self.testPassed("if(\"\")", "TRUE", "TRUE")
        if cond([]):
            await self.testFailed("if([])", "TRUE", "FALSE")
        else:
            await self.testPassed("if([])", "TRUE", "TRUE")
        await self.ensureIntegerEqual("(TRUE == TRUE)", (req(1, 1)), 1)
        await self.ensureIntegerEqual("(TRUE == FALSE)", (req(0, 1)), 0)
        await self.ensureIntegerEqual("(FALSE == TRUE)", (req(1, 0)), 0)
        await self.ensureIntegerEqual("(FALSE == FALSE)", (req(0, 0)), 1)
        await self.ensureIntegerEqual("(TRUE != TRUE)", (rneq(1, 1)), 0)
        await self.ensureIntegerEqual("(TRUE != FALSE)", (rneq(0, 1)), 1)
        await self.ensureIntegerEqual("(FALSE != TRUE)", (rneq(1, 0)), 1)
        await self.ensureIntegerEqual("(FALSE != FALSE)", (rneq(0, 0)), 0)
        await self.ensureIntegerEqual("(TRUE && TRUE)", (rbooland(1, 1)), 1)
        await self.ensureIntegerEqual("(TRUE && FALSE)", (rbooland(0, 1)), 0)
        await self.ensureIntegerEqual("(FALSE && TRUE)", (rbooland(1, 0)), 0)
        await self.ensureIntegerEqual("(FALSE && FALSE)", (rbooland(0, 0)), 0)
        await self.ensureIntegerEqual("(1 && 2)", (rbooland(2, 1)), 1)
        await self.ensureIntegerEqual("(1 && 0)", (rbooland(0, 1)), 0)
        await self.ensureIntegerEqual("(0 && 2)", (rbooland(2, 0)), 0)
        await self.ensureIntegerEqual("(0 && 0)", (rbooland(0, 0)), 0)
        await self.ensureIntegerEqual("(TRUE || TRUE)", (rboolor(1, 1)), 1)
        await self.ensureIntegerEqual("(TRUE || FALSE)", (rboolor(0, 1)), 1)
        await self.ensureIntegerEqual("(FALSE || TRUE)", (rboolor(1, 0)), 1)
        await self.ensureIntegerEqual("(FALSE || FALSE)", (rboolor(0, 0)), 0)
        await self.ensureIntegerEqual("(1 || 2)", (rboolor(2, 1)), 1)
        await self.ensureIntegerEqual("(1 || 0)", (rboolor(0, 1)), 1)
        await self.ensureIntegerEqual("(0 || 2)", (rboolor(2, 0)), 1)
        await self.ensureIntegerEqual("(0 || 0)", (rboolor(0, 0)), 0)
        await self.ensureIntegerEqual("(! TRUE)", (boolnot(1)), 0)
        await self.ensureIntegerEqual("(! FALSE)", (boolnot(0)), 1)
        await self.ensureIntegerEqual("(! 2)", (boolnot(2)), 0)
        await self.ensureIntegerEqual("(! 0)", (boolnot(0)), 1)
        await self.ensureIntegerEqual("(1 > 0)", (rgreater(0, 1)), 1)
        await self.ensureIntegerEqual("(0 > 1)", (rgreater(1, 0)), 0)
        await self.ensureIntegerEqual("(1 > 1)", (rgreater(1, 1)), 0)
        await self.ensureIntegerEqual("(0 < 1)", (rless(1, 0)), 1)
        await self.ensureIntegerEqual("(1 < 0)", (rless(0, 1)), 0)
        await self.ensureIntegerEqual("(1 < 1)", (rless(1, 1)), 0)
        await self.ensureIntegerEqual("(1 >= 0)", (rgeq(0, 1)), 1)
        await self.ensureIntegerEqual("(0 >= 1)", (rgeq(1, 0)), 0)
        await self.ensureIntegerEqual("(1 >= 1)", (rgeq(1, 1)), 1)
        await self.ensureIntegerEqual("(0 <= 1)", (rleq(1, 0)), 1)
        await self.ensureIntegerEqual("(1 <= 0)", (rleq(0, 1)), 0)
        await self.ensureIntegerEqual("(1 <= 1)", (rleq(1, 1)), 1)
        await self.ensureIntegerEqual("(10 & 25)", (rbitand(25, 10)), 8)
        await self.ensureIntegerEqual("(10 | 25)", (rbitor(25, 10)), 27)
        await self.ensureIntegerEqual("~10", bitnot(10), -11)
        await self.ensureIntegerEqual("(10 ^ 25)", (rbitxor(25, 10)), 19)
        await self.ensureIntegerEqual("(523 >> 2)", (rshr(2, 523)), 130)
        await self.ensureIntegerEqual("(523 << 2)", (rshl(2, 523)), 2092)
        await self.ensureIntegerEqual("(1 + 1)", (radd(1, 1)), 2)
        await self.ensureFloatEqual("(1 + 1.1)", (radd(1.1, 1.0)), 2.1)
        await self.ensureFloatEqual("(1.1 + 1)", (radd(1.0, 1.1)), 2.1)
        await self.ensureFloatEqual("(1.1 + 1.1)", (radd(1.1, 1.1)), 2.2)
        await self.ensureStringEqual("\"foo\" + \"bar\"", radd("bar", "foo"), "foobar")
        await self.ensureVectorEqual("(<1.1, 2.2, 3.3> + <4.4, 5.5, 6.6>)", (radd(Vector((4.4, 5.5, 6.6)), Vector((1.1, 2.2, 3.3)))), Vector((5.5, 7.7, 9.9)))
        await self.ensureRotationEqual("(<1.1, 2.2, 3.3, 4.4> + <4.4, 5.5, 6.6, 3.3>)", (radd(Quaternion((4.4, 5.5, 6.6, 3.3)), Quaternion((1.1, 2.2, 3.3, 4.4)))), Quaternion((5.5, 7.7, 9.9, 7.7)))
        await self.ensureListEqual("([1] + 2)", (radd(2, [1])), [1, 2])
        await self.ensureListEqual("([] + 1.5)", (radd(1.5, [])), [1.5])
        await self.ensureListEqual("([\"foo\"] + \"bar\")", (radd("bar", ["foo"])), ["foo", "bar"])
        await self.ensureListEqual("([] + <1,2,3>)", (radd(Vector((1.0, 2.0, 3.0)), [])), [Vector((1.0, 2.0, 3.0))])
        await self.ensureListEqual("([] + <1,2,3,4>)", (radd(Quaternion((1.0, 2.0, 3.0, 4.0)), [])), [Quaternion((1.0, 2.0, 3.0, 4.0))])
        await self.ensureListEqual("(1 + [2])", (radd([2], 1)), [1, 2])
        await self.ensureListEqual("(1.0 + [2])", (radd([2], 1.0)), [1.0, 2])
        await self.ensureListEqual("(1 + [2])", (radd([2], "one")), ["one", 2])
        await self.ensureListEqual("(<1.0,1.0,1.0,1.0> + [2])", (radd([2], Quaternion((1.0, 1.0, 1.0, 1.0)))), [Quaternion((1.0, 1.0, 1.0, 1.0)), 2])
        await self.ensureListEqual("(<1.0,1.0,1.0> + [2])", (radd([2], Vector((1.0, 1.0, 1.0)))), [Vector((1.0, 1.0, 1.0)), 2])
        _a = []
        _b = _a
        _a = radd(["foo"], _a)
        await self.ensureListEqual("list a = []; list b = a; a += [\"foo\"]; a == [\"foo\"]", _a, ["foo"])
        await self.ensureListEqual("list a = []; list b = a; a += [\"foo\"]; b == []", _b, [])
        _a = ["a"]
        _b = ["b"]
        _c = radd(_b, _a)
        await self.ensureListEqual("a = [\"a\"]; b = [\"b\"]; list c = a + b; a == [\"a\"];", _a, ["a"])
        await self.ensureListEqual("a = [\"a\"]; b = [\"b\"]; list c = a + b; b == [\"b\"];", _b, ["b"])
        await self.ensureListEqual("a = [\"a\"]; b = [\"b\"]; list c = a + b; c == [\"a\", \"b\"];", _c, ["a", "b"])
        await self.ensureIntegerEqual("(1 - 1)", (rsub(1, 1)), 0)
        await self.ensureFloatEqual("(1 - 0.5)", (rsub(0.5, 1.0)), 0.5)
        await self.ensureFloatEqual("(1.5 - 1)", (rsub(1.0, 1.5)), 0.5)
        await self.ensureFloatEqual("(2.2 - 1.1)", (rsub(1.1, 2.2)), 1.1)
        await self.ensureVectorEqual("(<1.5, 2.5, 3.5> - <4.5, 5.5, 6.5>)", (rsub(Vector((4.5, 5.5, 6.5)), Vector((1.5, 2.5, 3.5)))), Vector((-3.0, -3.0, -3.0)))
        await self.ensureRotationEqual("(<1.5, 2.5, 3.5, 4.5> - <4.5, 5.5, 6.5, 7.5>)", (rsub(Quaternion((4.5, 5.5, 6.5, 7.5)), Quaternion((1.5, 2.5, 3.5, 4.5)))), Quaternion((-3.0, -3.0, -3.0, -3.0)))
        await self.ensureIntegerEqual("(2 * 3)", (rmul(3, 2)), 6)
        await self.ensureFloatEqual("(2 * 3.5)", (rmul(3.5, 2.0)), 7.0)
        await self.ensureFloatEqual("(2.5 * 3)", (rmul(3.0, 2.5)), 7.5)
        await self.ensureFloatEqual("(2.5 * 3.5)", (rmul(3.5, 2.5)), 8.75)
        await self.ensureVectorEqual("(<1.1, 2.2, 3.3> * 2)", (rmul(2.0, Vector((1.1, 2.2, 3.3)))), Vector((2.2, 4.4, 6.6)))
        await self.ensureVectorEqual("(2 * <1.1, 2.2, 3.3>)", (rmul(2.0, Vector((1.1, 2.2, 3.3)))), (rmul(Vector((1.1, 2.2, 3.3)), 2.0)))
        await self.ensureVectorEqual("(<2.2, 4.4, 6.6> * 2.0)", (rmul(2.0, Vector((2.2, 4.4, 6.6)))), Vector((4.4, 8.8, 13.2)))
        await self.ensureVectorEqual("(2.0 * <2.2, 4.4, 6.6>)", (rmul(2.0, Vector((2.2, 4.4, 6.6)))), (rmul(Vector((2.2, 4.4, 6.6)), 2.0)))
        await self.ensureFloatEqual("<1,3,-5> * <4,-2,-1>", rmul(Vector((4.0, -2.0, -1.0)), Vector((1.0, 3.0, -5.0))), 3.0)
        await self.ensureVectorEqual("<-1,0,0> * <0, 0, 0.707, 0.707>", rmul(Quaternion((0.0, 0.0, 0.707, 0.707)), Vector((-1.0, 0.0, 0.0))), Vector((0.0, -1.0, 0.0)))
        await self.ensureRotationEqual("(<1.0, 2.0, 3.0, 4.0> * <5.0, 6.0, 7.0, 8.0>)", (rmul(Quaternion((5.0, 6.0, 7.0, 8.0)), Quaternion((1.0, 2.0, 3.0, 4.0)))), Quaternion((32.0, 32.0, 56.0, -6.0)))
        await self.ensureIntegerEqual("(2 / 2)", (rdiv(2, 2)), 1)
        await self.ensureFloatEqual("(2.2 / 2)", (rdiv(2.0, 2.2)), 1.1)
        await self.ensureFloatEqual("(3 / 1.5)", (rdiv(1.5, 3.0)), 2.0)
        await self.ensureFloatEqual("(2.2 / 2.0)", (rdiv(2.0, 2.2)), 1.1)
        await self.ensureVectorEqual("(<1.0, 2.0, 3.0> / 2)", (rdiv(2.0, Vector((1.0, 2.0, 3.0)))), Vector((0.5, 1.0, 1.5)))
        await self.ensureVectorEqual("(<3.0, 6.0, 9.0> / 1.5)", (rdiv(1.5, Vector((3.0, 6.0, 9.0)))), Vector((2.0, 4.0, 6.0)))
        await self.ensureVectorEqual("<-1,0,0> / <0, 0, 0.707, 0.707>", rdiv(Quaternion((0.0, 0.0, 0.707, 0.707)), Vector((-1.0, 0.0, 0.0))), Vector((0.0, 1.0, 0.0)))
        await self.ensureRotationEqual("(<1.0, 2.0, 3.0, 4.0> / <5.0, 6.0, 7.0, 8.0>)", (rdiv(Quaternion((5.0, 6.0, 7.0, 8.0)), Quaternion((1.0, 2.0, 3.0, 4.0)))), Quaternion((-16.0, 0.0, -8.0, 70.0)))
        await self.ensureIntegerEqual("(3 % 1)", (rmod(1, 3)), 0)
        await self.ensureVectorEqual("(<1.0, 2.0, 3.0> % <4.0, 5.0, 6.0>)", (rmod(Vector((4.0, 5.0, 6.0)), Vector((1.0, 2.0, 3.0)))), Vector((-3.0, 6.0, -3.0)))
        _i = 1
        await self.ensureIntegerEqual("i = 1;", _i, 1)
        _i = 1
        _i = radd(1, _i)
        await self.ensureIntegerEqual("i = 1; i += 1;", _i, 2)
        _i = 1
        _i = rsub(1, _i)
        await self.ensureIntegerEqual("i = 1; i -= 1;", _i, 0)
        _i = 2
        _i = rmul(2, _i)
        await self.ensureIntegerEqual("i = 2; i *= 2;", _i, 4)
        _i = 1
        (_i := typecast(rmul(0.5, _i), int))
        await self.ensureIntegerEqual("i = 1; i *= 0.5;", _i, 0)
        _i = 2
        _i = rdiv(2, _i)
        await self.ensureIntegerEqual("i = 2; i /= 2;", _i, 1)
        _i = rdiv(-1, -2147483648)
        await self.ensureIntegerEqual("i = 0x80000000 / -1;", _i, -2147483648)
        _i = 3
        _i = rmod(1, _i)
        await self.ensureIntegerEqual("i = 3; i %= 1;", _i, 0)
        _i = rmod(-1, -2147483648)
        await self.ensureIntegerEqual("i = 0x80000000 % -1;", _i, 0)
        _i = 1
        await self.ensureIntegerEqual("postinc", rbooland((req(1, postincr(locals(), "_i"))), (req(2, _i))), 1)
        _i = 1
        await self.ensureIntegerEqual("preinc", rbooland((req(2, preincr(locals(), "_i"))), (req(2, _i))), 1)
        _i = 2
        await self.ensureIntegerEqual("postdec", rbooland((req(2, postdecr(locals(), "_i"))), (req(1, _i))), 1)
        _i = 2
        await self.ensureIntegerEqual("predec1", rbooland((req(1, predecr(locals(), "_i"))), (req(1, _i))), 1)
        _i = 2
        _i -= 1
        await self.ensureIntegerEqual("predec2", _i, 1)
        await self.ensureFloatEqual("((float)2)", (2.0), 2.0)
        await self.ensureStringEqual("((string)2)", (typecast(2, str)), "2")
        await self.ensureIntegerEqual("((integer) 1.5)", (typecast(1.5, int)), 1)
        await self.ensureStringEqual("((string) 1.5)", (typecast(1.5, str)), "1.500000")
        await self.ensureIntegerEqual("((integer) \"0xF\")", (typecast("0xF", int)), 15)
        await self.ensureIntegerEqual("((integer) \"2\")", (typecast("2", int)), 2)
        await self.ensureFloatEqual("((float) \"1.5\")", (typecast("1.5", float)), 1.5)
        await self.ensureVectorEqual("((vector) \"<1,2,3>\")", (typecast("<1,2,3>", Vector)), Vector((1.0, 2.0, 3.0)))
        await self.ensureRotationEqual("((quaternion) \"<1,2,3,4>\")", (typecast("<1,2,3,4>", Quaternion)), Quaternion((1.0, 2.0, 3.0, 4.0)))
        await self.ensureStringEqual("((string) <1,2,3>)", (typecast(Vector((1.0, 2.0, 3.0)), str)), "<1.00000, 2.00000, 3.00000>")
        await self.ensureStringEqual("((string) <1,2,3,4>)", (typecast(Quaternion((1.0, 2.0, 3.0, 4.0)), str)), "<1.00000, 2.00000, 3.00000, 4.00000>")
        await self.ensureStringEqual("((string) [1,2.5,<1,2,3>])", (typecast([1, 2.5, Vector((1.0, 2.0, 3.0))], str)), "12.500000<1.000000, 2.000000, 3.000000>")
        _i = 0
        while cond(rless(10, _i)):
            _i += 1
        await self.ensureIntegerEqual("i = 0; while(i < 10) ++i", _i, 10)
        _i = 0
        while True == True:
            _i += 1
            if not cond(rless(10, _i)):
                break
        await self.ensureIntegerEqual("i = 0; do {++i;} while(i < 10);", _i, 10)
        _i = 0
        while True == True:
            if not cond(rless(10, _i)):
                break
            pass
            _i += 1
        await self.ensureIntegerEqual("for(i = 0; i < 10; ++i);", _i, 10)
        _i = 1
        goto ._SkipAssign
        await self.builtin_funcs.llSetText("Error", Vector((1.0, 0.0, 0.0)), 1.0)
        _i = 2
        label ._SkipAssign
        await self.ensureIntegerEqual("assignjump", _i, 1)
        await self.ensureIntegerEqual("testReturn()", await self.testReturn(), 1)
        await self.ensureFloatEqual("testReturnFloat()", await self.testReturnFloat(), 1.0)
        await self.ensureStringEqual("testReturnString()", await self.testReturnString(), "Test string")
        await self.ensureVectorEqual("testReturnVector()", await self.testReturnVector(), Vector((1.0, 2.0, 3.0)))
        await self.ensureRotationEqual("testReturnRotation()", await self.testReturnRotation(), Quaternion((1.0, 2.0, 3.0, 4.0)))
        await self.ensureListEqual("testReturnList()", await self.testReturnList(), [1, 2, 3])
        await self.ensureVectorEqual("testReturnVectorNested()", await self.testReturnVectorNested(), Vector((1.0, 2.0, 3.0)))
        await self.ensureVectorEqual("libveccall", await self.testReturnVectorWithLibraryCall(), Vector((1.0, 2.0, 3.0)))
        await self.ensureRotationEqual("librotcall", await self.testReturnRotationWithLibraryCall(), Quaternion((1.0, 2.0, 3.0, 4.0)))
        await self.ensureIntegerEqual("testParameters(1)", await self.testParameters(1), 2)
        _i = 1
        await self.ensureIntegerEqual("i = 1; testParameters(i)", await self.testParameters(_i), 2)
        await self.ensureIntegerEqual("testRecursion(10)", await self.testRecursion(10), 0)
        await self.ensureIntegerEqual("gInteger", self.gInteger, 5)
        await self.ensureFloatEqual("gFloat", self.gFloat, 1.5)
        await self.ensureStringEqual("gString", self.gString, "foo")
        await self.ensureVectorEqual("gVector", self.gVector, Vector((1.0, 2.0, 3.0)))
        await self.ensureRotationEqual("gRot", self.gRot, Quaternion((1.0, 2.0, 3.0, 4.0)))
        await self.ensureListEqual("gList", self.gList, [1, 2, 3])
        self.gInteger = 1
        await self.ensureIntegerEqual("gInteger = 1", self.gInteger, 1)
        self.gFloat = 0.5
        await self.ensureFloatEqual("gFloat = 0.5", self.gFloat, 0.5)
        self.gString = "bar"
        await self.ensureStringEqual("gString = \"bar\"", self.gString, "bar")
        self.gVector = Vector((3.0, 3.0, 3.0))
        await self.ensureVectorEqual("gVector = <3,3,3>", self.gVector, Vector((3.0, 3.0, 3.0)))
        self.gRot = Quaternion((3.0, 3.0, 3.0, 3.0))
        await self.ensureRotationEqual("gRot = <3,3,3,3>", self.gRot, Quaternion((3.0, 3.0, 3.0, 3.0)))
        self.gList = [4, 5, 6]
        await self.ensureListEqual("gList = [4,5,6]", self.gList, [4, 5, 6])
        self.gVector = Vector((3.0, 3.0, 3.0))
        await self.ensureVectorEqual("-gVector = <-3,-3,-3>", neg(self.gVector), Vector((-3.0, -3.0, -3.0)))
        self.gRot = Quaternion((3.0, 3.0, 3.0, 3.0))
        await self.ensureRotationEqual("-gRot = <-3,-3,-3,-3>", neg(self.gRot), Quaternion((-3.0, -3.0, -3.0, -3.0)))
        _v = Vector((0.0, 0.0, 0.0))
        _v = replace_coord_axis(_v, 0, 3.0)
        await self.ensureFloatEqual("v.x", _v[0], 3.0)
        _q = Quaternion((0.0, 0.0, 0.0, 1.0))
        _q = replace_coord_axis(_q, 3, 5.0)
        await self.ensureFloatEqual("q.s", _q[3], 5.0)
        self.gVector = replace_coord_axis(self.gVector, 1, 17.5)
        await self.ensureFloatEqual("gVector.y = 17.5", self.gVector[1], 17.5)
        self.gRot = replace_coord_axis(self.gRot, 2, 19.5)
        await self.ensureFloatEqual("gRot.z = 19.5", self.gRot[2], 19.5)
        _l = typecast(5, list)
        _l2 = typecast(5, list)
        await self.ensureListEqual("leq1", _l, _l2)
        await self.ensureListEqual("leq2", _l, [5])
        await self.ensureListEqual("leq3", [1.5, 6, Vector((1.0, 2.0, 3.0)), Quaternion((1.0, 2.0, 3.0, 4.0))], [1.5, 6, Vector((1.0, 2.0, 3.0)), Quaternion((1.0, 2.0, 3.0, 4.0))])
        await self.ensureIntegerEqual("sesc1", await self.builtin_funcs.llStringLength("\\"), 1)
        await self.ensureIntegerEqual("sesc2", await self.builtin_funcs.llStringLength("    "), 4)
        await self.ensureIntegerEqual("sesc3", await self.builtin_funcs.llStringLength("\n"), 1)
        await self.ensureIntegerEqual("sesc4", await self.builtin_funcs.llStringLength("\""), 1)
        await self.ensureStringEqual("testExpressionLists([testExpressionLists([]), \"bar\"]) == \"foofoobar\"", await self.testExpressionLists([await self.testExpressionLists([]), "bar"]), "foofoobar")
        if cond(rboolor(1, rbooland(rbitor(rbitxor(rdiv(await self.callOrderFunc(5), await self.callOrderFunc(4)), await self.callOrderFunc(3)), await self.callOrderFunc(2)), rboolor(rmul(await self.callOrderFunc(1), await self.callOrderFunc(0)), 1)))):
            pass
        await self.ensureListEqual("gCallOrder expected order", self.gCallOrder, [5, 4, 3, 2, 1, 0])
        await self.ensureIntegerEqual("(gInteger = 5)", (assign(self.__dict__, "gInteger", 5)), 5)
        await self.ensureFloatEqual("(gVector.z = 6)", (assign(self.__dict__, "gVector", replace_coord_axis(self.gVector, 2, 6.0))[2]), 6.0)
        self.gVector = Vector((1.0, 2.0, 3.0))
        await self.ensureFloatEqual("++gVector.z", preincr(self.__dict__, "gVector", 2), 4.0)
        self.gVector = Vector((1.0, 2.0, 3.0))
        await self.ensureFloatEqual("gVector.z++", postincr(self.__dict__, "gVector", 2), 3.0)
        await self.ensureFloatEqual("(v.z = 6)", ((_v := replace_coord_axis(_v, 2, 6.0))[2]), 6.0)
        _v = Vector((1.0, 2.0, 3.0))
        await self.ensureFloatEqual("++v.z", preincr(locals(), "_v", 2), 4.0)
        _v = Vector((1.0, 2.0, 3.0))
        await self.ensureFloatEqual("v.z++", postincr(locals(), "_v", 2), 3.0)
        await self.ensureFloatEqual("posinf == posinf", float("inf"), float("inf"))
        await self.ensureFloatEqual("neginf == neginf", float("-inf"), float("-inf"))
        await self.ensureFalse("posinf != neginf", req(float("-inf"), float("inf")))
        await self.ensureStringEqual("(string)posinf == 'Infinity'", typecast(float("inf"), str), "Infinity")
        await self.ensureStringEqual("(string)neginf == '-Infinity'", typecast(float("-inf"), str), "-Infinity")

    async def runTests(self) -> None:
        self.gInteger = 5
        self.gFloat = 1.5
        self.gString = "foo"
        self.gVector = Vector((1.0, 2.0, 3.0))
        self.gRot = Quaternion((1.0, 2.0, 3.0, 4.0))
        self.gList = [1, 2, 3]
        self.gTestsPassed = 0
        self.gTestsFailed = 0
        self.gCallOrder = []
        await self.tests()
        print("All tests passed")

    async def edefaultstate_entry(self) -> None:
        await self.runTests()

