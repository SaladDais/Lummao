# Lightly modified version of https://github.com/insignification/python-goto
# this is public domain / CC0 / 0BSD / whatever is legal in the EU.

import dis
import struct
import array
import sys
import types
import functools
import weakref
import warnings

try:
    _array_to_bytes = array.array.tobytes
except AttributeError:
    _array_to_bytes = array.array.tostring


class _Bytecode:
    def __init__(self):
        x, y = None, None
        code = (lambda: x if x else y).__code__.co_code
        opcode, oparg = struct.unpack_from('BB', code, 2)

        # Starting with Python 3.6, the bytecode format has been changed to use
        # 16-bit words (8-bit opcode + 8-bit argument) for each instruction,
        # as opposed to previously 24-bit (8-bit opcode + 16-bit argument) for
        # instructions that expect an argument or just 8-bit for those that don't.
        # https://bugs.python.org/issue26647
        if dis.opname[opcode] == 'POP_JUMP_IF_FALSE':
            self.argument = struct.Struct('B')
            self.have_argument = 0
            # As of Python 3.6, jump targets are still addressed by their byte
            # unit. This, however, is matter to change, so that jump targets,
            # in the future, will refer to the code unit (address in bytes / 2).
            # https://bugs.python.org/issue26647
            self.jump_unit = 8 // oparg
        else:
            self.argument = struct.Struct('<H')
            self.have_argument = dis.HAVE_ARGUMENT
            self.jump_unit = 1

        self.has_loop_blocks = 'SETUP_LOOP' in dis.opmap
        self.has_pop_except = 'POP_EXCEPT' in dis.opmap
        self.has_setup_with = 'SETUP_WITH' in dis.opmap
        self.has_setup_except = 'SETUP_EXCEPT' in dis.opmap
        self.has_begin_finally = 'BEGIN_FINALLY' in dis.opmap
        self.has_with_except = 'WITH_EXCEPT_START' in dis.opmap

        try:
            import __pypy__
            self.pypy_finally_semantics = True
        except ImportError:
            self.pypy_finally_semantics = False

    @property
    def argument_bits(self):
        return self.argument.size * 8


_BYTECODE = _Bytecode()

# use a weak dictionary in case code objects can be garbage-collected
_patched_code_cache = weakref.WeakKeyDictionary()
try:
    _patched_code_cache[_Bytecode.__init__.__code__] = None
except TypeError:
    _patched_code_cache = {}  # ...unless not supported


def _make_code(code, codestring, data):
    try:
        # code.replace is new in 3.8+
        return code.replace(co_code=codestring,
                            co_nlocals=data.nlocals,
                            co_varnames=data.varnames,
                            co_consts=data.consts,
                            co_names=data.names)
    except:
        args = [
            code.co_argcount, data.nlocals, code.co_stacksize,
            code.co_flags, codestring, data.consts,
            data.names, data.varnames, code.co_filename,
            code.co_name, code.co_firstlineno, code.co_lnotab,
            code.co_freevars, code.co_cellvars
        ]

        try:
            args.insert(1, code.co_kwonlyargcount)  # PY3
        except AttributeError:
            pass

        return types.CodeType(*args)


def _parse_instructions(code, yield_nones_at_end=0):
    extended_arg = 0
    extended_arg_offset = None
    pos = 0

    while pos < len(code):
        offset = pos
        if extended_arg_offset is not None:
            offset = extended_arg_offset

        opcode = struct.unpack_from('B', code, pos)[0]
        pos += 1

        oparg = None
        if opcode >= _BYTECODE.have_argument:
            oparg = extended_arg | _BYTECODE.argument.unpack_from(code, pos)[0]
            pos += _BYTECODE.argument.size

            if opcode == dis.EXTENDED_ARG:
                extended_arg = oparg << _BYTECODE.argument_bits
                extended_arg_offset = offset
                continue

        extended_arg = 0
        extended_arg_offset = None
        yield dis.opname[opcode], oparg, offset

    for _ in range(yield_nones_at_end):
        yield None, None, None


def _get_instruction_size(opname, oparg=0):
    size = 1

    extended_arg = oparg >> _BYTECODE.argument_bits
    if extended_arg != 0:
        size += _get_instruction_size('EXTENDED_ARG', extended_arg)
        oparg &= (1 << _BYTECODE.argument_bits) - 1

    opcode = dis.opmap[opname]
    if opcode >= _BYTECODE.have_argument:
        size += _BYTECODE.argument.size

    return size


def _get_instructions_size(ops):
    size = 0
    for op in ops:
        if isinstance(op, str):
            size += _get_instruction_size(op)
        else:
            size += _get_instruction_size(*op)
    return size


def _write_instruction(buf, pos, opname, oparg=0):
    extended_arg = oparg >> _BYTECODE.argument_bits
    if extended_arg != 0:
        pos = _write_instruction(buf, pos, 'EXTENDED_ARG', extended_arg)
        oparg &= (1 << _BYTECODE.argument_bits) - 1

    opcode = dis.opmap[opname]
    buf[pos] = opcode
    pos += 1

    if opcode >= _BYTECODE.have_argument:
        _BYTECODE.argument.pack_into(buf, pos, oparg)
        pos += _BYTECODE.argument.size

    return pos


def _write_instructions(buf, pos, ops):
    for op in ops:
        if isinstance(op, str):
            pos = _write_instruction(buf, pos, op)
        else:
            pos = _write_instruction(buf, pos, *op)
    return pos


def _warn_bug(msg):
    warnings.warn("Internal error detected"
                  + " - result of with_goto may be incorrect. (%s)" % msg)


def _find_labels_and_gotos(code):
    labels = {}
    gotos = []

    block_stack = []
    block_counter = 0
    last_block = None

    opname1 = oparg1 = offset1 = None
    opname2 = oparg2 = offset2 = None
    opname3 = oparg3 = offset3 = None

    def replace_block_in_stack(stack, old_block, new_block):
        for i, block in enumerate(stack):
            if block == old_block:
                stack[i] = new_block

    def replace_block(old_block, new_block):
        replace_block_in_stack(block_stack, old_block, new_block)
        for label_target in labels:
            replace_block_in_stack(labels[label_target][2], old_block, new_block)
        for g in gotos:
            replace_block_in_stack(g[3], old_block, new_block)

    def push_block(opname, target_offset=None):
        new_counter = block_counter + 1
        block_stack.append((opname, target_offset, new_counter))
        return new_counter  # to be assigned to block_counter

    def pop_block():
        if block_stack:
            return block_stack.pop()
        else:
            _warn_bug("can't pop block")

    def pop_block_of_type(typ):
        if block_stack and block_stack[-1][0] != typ:
            # in 3.8, only finally blocks are supported, so we must determine
            # except/finally ourselves, and replace the block's type
            if not _BYTECODE.has_setup_except and \
                    typ == "<EXCEPT>" and \
                    block_stack[-1][0] == '<FINALLY>':
                replace_block(block_stack[-1], (typ,) + block_stack[-1][1:])
            else:
                _warn_bug("mismatched block type")
        return pop_block()

    jump_targets = set(dis.findlabels(code.co_code))
    dead = False

    for opname4, oparg4, offset4 in _parse_instructions(code.co_code, 3):
        endoffset1 = offset2

        if offset1 in jump_targets:
            dead = False

        # check for block exits
        while block_stack and offset1 == block_stack[-1][1]:
            exitname, _, _ = last_block = pop_block()

            if exitname == 'SETUP_EXCEPT' and _BYTECODE.has_pop_except:
                block_counter = push_block('<EXCEPT>')
            elif exitname == 'SETUP_FINALLY':
                block_counter = push_block('<FINALLY>')

        # check for special opcodes
        if opname1 in ('LOAD_GLOBAL', 'LOAD_NAME'):
            if opname2 == 'LOAD_ATTR' and opname3 == 'POP_TOP':
                name = code.co_names[oparg1]
                if name == 'label':
                    if oparg2 in labels:
                        co_name = code.co_names[oparg2]
                        raise SyntaxError('Ambiguous label {0!r}'.format(co_name))
                    labels[oparg2] = (offset1,
                                      offset4,
                                      list(block_stack))
                elif name == 'goto':
                    gotos.append((offset1,
                                  offset4,
                                  oparg2,
                                  list(block_stack),
                                  0))
            elif opname2 == 'LOAD_ATTR' and opname3 == 'STORE_ATTR':
                if code.co_names[oparg1] == 'goto' and \
                        code.co_names[oparg2] in ('param', 'params'):
                    gotos.append((offset1,
                                  offset4,
                                  oparg3,
                                  list(block_stack),
                                  code.co_names[oparg2]))

        elif opname1 in ('SETUP_LOOP', 'FOR_ITER',
                         'SETUP_EXCEPT', 'SETUP_FINALLY',
                         'SETUP_WITH', 'SETUP_ASYNC_WITH'):
            if opname1 == 'SETUP_FINALLY' and sys.version_info >= (3, 9):
                raise NotImplementedError("finally semantics not supported in 3.9+")
            # Make sure to convert the argument to the real offset using the given version's jump units
            block_counter = push_block(opname1, endoffset1 + (oparg1 * _BYTECODE.jump_unit))

        elif opname1 == 'POP_EXCEPT':
            last_block = pop_block_of_type('<EXCEPT>')

        elif opname1 == 'END_FINALLY' and not dead:
            # (python compilers put dead END_FINALLY's in weird places)
            last_block = pop_block_of_type('<FINALLY>')

        elif opname1 in ('WITH_CLEANUP', 'WITH_CLEANUP_START'):
            if _BYTECODE.has_setup_with:
                # temporary block to match END_FINALLY
                block_counter = push_block('<FINALLY>')
            else:
                # python 2.6 - finally was actually with
                replace_block(last_block, ('SETUP_WITH',) + last_block[1:])

        elif opname1 == 'WITH_EXCEPT_START':
            # Python 3.9+
            # https://github.com/python/cpython/issues/77568
            raise NotImplementedError("with/finally semantics not supported in Python 3.9+")

        if opname1 in ('JUMP_ABSOLUTE', 'JUMP_FORWARD'):
            dead = True

        opname1, oparg1, offset1 = opname2, oparg2, offset2
        opname2, oparg2, offset2 = opname3, oparg3, offset3
        opname3, oparg3, offset3 = opname4, oparg4, offset4

    if block_stack:
        _warn_bug("block stack not empty")

    return labels, gotos


def _inject_nop_sled(buf, pos, end):
    while pos < end:
        pos = _write_instruction(buf, pos, 'NOP')


def _inject_ops(buf, pos, end, ops):
    size = _get_instructions_size(ops)

    if pos + size > end:
        # not enough space, add code at buffer end and jump there
        buf_end = len(buf)

        go_to_end_ops = [('JUMP_ABSOLUTE', buf_end // _BYTECODE.jump_unit)]

        if pos + _get_instructions_size(go_to_end_ops) > end:
            # not sure if reachable
            raise SyntaxError('Goto in an incredibly huge function')

        pos = _write_instructions(buf, pos, go_to_end_ops)
        _inject_nop_sled(buf, pos, end)

        buf.extend([0] * size)
        _write_instructions(buf, buf_end, ops)
    else:
        pos = _write_instructions(buf, pos, ops)
        _inject_nop_sled(buf, pos, end)


class _CodeData:
    def __init__(self, code):
        self.nlocals = code.co_nlocals
        self.varnames = code.co_varnames
        self.consts = code.co_consts
        self.names = code.co_names

    def get_const(self, value):
        try:
            i = self.consts.index(value)
        except ValueError:
            i = len(self.consts)
            self.consts += (value,)
        return i

    def get_name(self, value):
        try:
            i = self.names.index(value)
        except ValueError:
            i = len(self.names)
            self.names += (value,)
        return i

    def add_var(self, name):
        idx = len(self.varnames)
        self.varnames += (name,)
        self.nlocals += 1
        return idx


def _patch_code(code):
    new_code = _patched_code_cache.get(code)
    if new_code is not None:
        return new_code

    labels, gotos = _find_labels_and_gotos(code)
    buf = array.array('B', code.co_code)
    temp_var = None
    many_params = False

    data = _CodeData(code)

    for pos, end, _ in labels.values():
        _inject_nop_sled(buf, pos, end)

    for pos, end, label_target, origin_stack, params in gotos:
        try:
            _, target, target_stack = labels[label_target]
        except KeyError:
            raise SyntaxError('Unknown label {0!r}'.format(code.co_names[label_target]))

        ops = []

        # prepare
        common_depth = min(len(origin_stack), len(target_stack))
        for i in range(common_depth):
            if origin_stack[i] != target_stack[i]:
                common_depth = i
                break

        if params:
            if temp_var is None:
                temp_var = data.add_var('goto.temp')

            # must do this before any blocks are pushed/popped
            ops.append(('STORE_FAST', temp_var))
            many_params = (params != 'param')

        # pop blocks
        for block, _, _ in reversed(origin_stack[common_depth:]):
            if block == 'FOR_ITER':
                if not _BYTECODE.has_loop_blocks:
                    ops.append('POP_TOP')
            elif block == '<EXCEPT>':
                ops.append('POP_EXCEPT')
            elif block == '<FINALLY>':
                ops.append('END_FINALLY')
            else:
                ops.append('POP_BLOCK')
                if block in ('SETUP_WITH', 'SETUP_ASYNC_WITH'):
                    ops.append('POP_TOP')
                # pypy 3.6 keeps a block around until END_FINALLY;
                # python 3.8 reuses SETUP_FINALLY for SETUP_EXCEPT
                # (where END_FINALLY is not accepted).
                # What will pypy 3.8 do?
                if _BYTECODE.pypy_finally_semantics and \
                        block in ('SETUP_FINALLY', 'SETUP_WITH',
                                  'SETUP_ASYNC_WITH'):
                    if _BYTECODE.has_begin_finally:
                        ops.append('BEGIN_FINALLY')
                    else:
                        ops.append(('LOAD_CONST', data.get_const(None)))
                    ops.append('END_FINALLY')

        # push blocks
        def setup_block_absolute(block_offset, block_end):
            # there's no SETUP_*_ABSOLUTE, so we setup forward to an JUMP_ABSOLUTE
            jump_abs_op = ('JUMP_ABSOLUTE', block_end)
            skip_jump_op = ('JUMP_FORWARD', _get_instruction_size(*jump_abs_op))
            setup_block_op = (block_offset, _get_instruction_size(*skip_jump_op))
            ops.extend((setup_block_op, skip_jump_op, jump_abs_op))

        tuple_i = 0
        for block, block_target, _ in target_stack[common_depth:]:
            if block in ('FOR_ITER', 'SETUP_WITH', 'SETUP_ASYNC_WITH'):
                if not params:
                    raise SyntaxError(
                        'Jump into block without the necessary params')

                ops.append(('LOAD_FAST', temp_var))
                if many_params:
                    ops.append(('LOAD_CONST', data.get_const(tuple_i)))
                    ops.append('BINARY_SUBSCR')
                tuple_i += 1

                if block == 'FOR_ITER':
                    # this both converts iterables to iterators for
                    # convenience, and prevents FOR_ITER from crashing
                    # on non-iter objects. (this is a no-op for iterators)
                    ops.append('GET_ITER')

                elif block in ('SETUP_WITH', 'SETUP_ASYNC_WITH'):
                    # SETUP_WITH executes __enter__ and so would be
                    # inappropriate
                    # (a goto must bypass any and all side-effects)
                    ops.append(('LOAD_ATTR', data.get_name('__exit__')))
                    setup_block_absolute('SETUP_FINALLY', block_target)

            elif block in ('SETUP_LOOP', 'SETUP_EXCEPT', 'SETUP_FINALLY'):
                setup_block_absolute(block, block_target)

            elif block == '<FINALLY>':
                if _BYTECODE.pypy_finally_semantics:
                    ops.append('SETUP_FINALLY')
                    ops.append('POP_BLOCK')
                if _BYTECODE.has_begin_finally:
                    ops.append('BEGIN_FINALLY')
                else:
                    ops.append(('LOAD_CONST', data.get_const(None)))

            elif block == '<EXCEPT>':
                # we raise an exception to get the right block pushed
                raise_ops = [('LOAD_CONST', data.get_const(None)),
                             ('RAISE_VARARGS', 1)]

                setup_except = 'SETUP_EXCEPT' if _BYTECODE.has_setup_except else \
                    'SETUP_FINALLY'
                ops.append((setup_except, _get_instructions_size(raise_ops)))
                ops += raise_ops
                for _ in range(3):
                    ops.append("POP_TOP")

            else:
                _warn_bug("ignoring %s" % block)

        ops.append(('JUMP_ABSOLUTE', target // _BYTECODE.jump_unit))

        _inject_ops(buf, pos, end, ops)

    new_code = _make_code(code, _array_to_bytes(buf), data)

    _patched_code_cache[code] = new_code
    return new_code


def with_goto(func_or_code):
    if isinstance(func_or_code, types.CodeType):
        return _patch_code(func_or_code)

    return functools.update_wrapper(
        types.FunctionType(
            _patch_code(func_or_code.__code__),
            func_or_code.__globals__,
            func_or_code.__name__,
            func_or_code.__defaults__,
            func_or_code.__closure__,
        ),
        func_or_code
    )


class _CatchAll:
    __slots__ = []

    def __getattribute__(self, item):
        raise RuntimeError("Unpatched goto for " + item)


# Not strictly necessary, but stops linters from freaking out.
label = _CatchAll()
goto = _CatchAll()
