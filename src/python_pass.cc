#include <cmath>
#include <fstream>

#include "python_pass.hh"

using namespace Tailslide;

static const char * const PY_TYPE_NAMES[LST_MAX] {
  "None",
  "int",
  "float",
  "str",
  "Key",
  "Vector",
  "Quaternion",
  "list",
  "<ERROR>"
};

static const char * const PY_PRELUDE_TYPE_NAMES[LST_MAX] {
  "None",
  "int",
  "float",
  "Optional[str]",
  "Optional[Key]",
  "Vector",
  "Quaternion",
  "Optional[list]",
  "<ERROR>"
};

class ScopedTabSetter {
  public:
    ScopedTabSetter(PythonVisitor *visitor, int tabs): _mOldTabs(visitor->mTabs), _mVisitor(visitor) {
      _mVisitor->mTabs = tabs;
    };
    ~ScopedTabSetter() {
      _mVisitor->mTabs = _mOldTabs;
    }
  private:
    int _mOldTabs;
    PythonVisitor *_mVisitor;
};



void PythonVisitor::writeChildrenSep(LSLASTNode *parent, const char *separator) {
  for (auto *child: *parent) {
    child->visit(this);
    if (child->getNext())
      mStr << separator;
  }
}

const std::string INF_STR = "inf";
const std::string NEG_INF_STR = "-inf";
const std::set<std::string> NAN_STRS {
    "nan",
    "-nan",
    "-nan(ind)",
    "nan(ind)"
};

void PythonVisitor::writeFloat(float f_val) {
  bool special_repr = false;
  std::string s_val(std::to_string(f_val));

  if (s_val == INF_STR || s_val == NEG_INF_STR) {
    special_repr = true;
  // Only one kind of NaN in LSL!
  } else if (NAN_STRS.find(s_val) != NAN_STRS.end()) {
    s_val = "nan";
    special_repr = true;
  }

  if (special_repr) {
    mStr << "float(\"" << s_val << "\")";
    return;
  }

  // strip insignificant trailing zeroes from the string form
  auto non_zero_pos = s_val.find_last_not_of('0');
  auto decimal_pos = s_val.find_last_of('.');
  // there is a decimal
  if (decimal_pos != std::string::npos) {
    if (non_zero_pos == decimal_pos) {
      // 5.00000
      s_val.erase(non_zero_pos + 2, std::string::npos);
    } else if (non_zero_pos > decimal_pos) {
      // 1.50000, but not 103.55555
      s_val.erase(non_zero_pos + 1, std::string::npos);
    }
  }

  if (std::stof(s_val) == f_val && std::isfinite(f_val)) {
    // The float is exactly representable in the string form,
    // just print that out.
    mStr << s_val;
    return;
  }

  // This float is hard to represent as a string without losing precision.
  // Write in host-endian binary form to preserve precision
  auto *b_val = reinterpret_cast<uint8_t *>(&f_val);
  const size_t hex_val_len = (4 * 2) + 1;
  char hex_val[hex_val_len] = {0};
  snprintf(
      (char *)&hex_val,
      hex_val_len,
      "%02x%02x%02x%02x",
      b_val[0], b_val[1], b_val[2], b_val[3]
  );
  // the human-readable float val is first in the tuple, but it isn't actually used, it's only there
  // for readability.
  mStr << "bin2float('" << s_val << "', '" << (const char*)&hex_val << "')";
}

std::string PythonVisitor::getSymbolName(LSLSymbol *sym) {
  switch (sym->getSubType()) {
    // Stop common stuff from colliding with Python builtins (not a good solution!)
    case SYM_LOCAL:
    case SYM_FUNCTION_PARAMETER:
    case SYM_EVENT_PARAMETER:
      return std::string("_") + sym->getName();
    default:
      return sym->getName();
  }
}

bool PythonVisitor::visit(LSLScript *script) {
  // Need to make any casts explicit
  class DeSugaringVisitor de_sugaring_visitor(script->mContext->allocator, true);
  script->visit(&de_sugaring_visitor);
  mStr << "from lummao import *\n\n\n";
  mStr << "class Script(BaseLSLScript):\n";
  // everything after this must be indented
  ScopedTabSetter tab_setter(this, mTabs + 1);

  // put the type declarations for global vars at the class level
  for (auto *glob : *script->getGlobals()) {
    if (glob->getNodeType() != NODE_GLOBAL_VARIABLE)
      continue;
    auto *glob_var = (LSLGlobalVariable *)glob;
    auto *sym = glob_var->getSymbol();
    doTabs();
    mStr << getSymbolName(sym) << ": " << PY_TYPE_NAMES[sym->getIType()] << '\n';
  }

  mStr << '\n';
  // then generate an __init__() where they're actually initialized
  doTabs();
  mStr << "def __init__(self):\n";
  {
    // needs to be indented one more level within the __init__()
    ScopedTabSetter tab_setter_2(this, mTabs + 1);
    doTabs();
    mStr << "super().__init__()\n";
    for (auto *glob: *script->getGlobals()) {
      if (glob->getNodeType() != NODE_GLOBAL_VARIABLE)
        continue;
      glob->visit(this);
    }
    mStr << '\n';
  }

  // now the global functions
  for (auto *glob : *script->getGlobals()) {
    if (glob->getNodeType() != NODE_GLOBAL_FUNCTION)
      continue;
    glob->visit(this);
  }

  // and the states and their event handlers
  script->getStates()->visit(this);
  return false;
}

bool PythonVisitor::visit(LSLGlobalVariable *glob_var) {
  auto *sym = glob_var->getSymbol();
  doTabs();
  mStr << "self." << getSymbolName(sym) << " = ";
  LSLASTNode *initializer = glob_var->getInitializer();
  if (!initializer) {
    initializer = sym->getType()->getDefaultValue();
  }
  initializer->visit(this);
  mStr << "\n";
  return false;
}

bool PythonVisitor::visit(LSLGlobalFunction *glob_func) {
  auto *func_sym = glob_func->getSymbol();
  if (func_sym->getHasJumps()) {
    doTabs();
    mStr << "@with_goto\n";
  }
  doTabs();
  mStr << "async def " << getSymbolName(func_sym) << "(self";
  for (auto *arg : *glob_func->getArguments()) {
    auto *arg_sym = arg->getSymbol();
    mStr << ", " << getSymbolName(arg_sym) << ": " << PY_TYPE_NAMES[arg_sym->getIType()];
  }
  mStr << ") -> " << PY_TYPE_NAMES[func_sym->getIType()] << ":\n";
  visitFuncLike(glob_func, glob_func->getStatements());
  return false;
}

bool PythonVisitor::visit(LSLEventHandler *event_handler) {
  auto *state_sym = event_handler->getParent()->getParent()->getSymbol();
  auto *id = event_handler->getIdentifier();
  auto *func_sym = event_handler->getSymbol();
  if (func_sym->getHasJumps()) {
    doTabs();
    mStr << "@with_goto\n";
  }
  doTabs();
  mStr << "async def e" << getSymbolName(state_sym) << id->getName() << "(self";
  for (auto *arg : *event_handler->getArguments()) {
    auto *arg_sym = arg->getSymbol();
    mStr << ", " << getSymbolName(arg_sym) << ": " << PY_TYPE_NAMES[arg_sym->getIType()];
  }
  mStr << ") -> " << PY_TYPE_NAMES[id->getIType()] << ":\n";
  visitFuncLike(event_handler, event_handler->getStatements());
  return false;
}

void PythonVisitor::visitFuncLike(LSLASTNode *func_like, LSLASTNode *body) {
  ScopedTabSetter tab_setter(this, mTabs + 1);
  _mFuncPreludeTabs = mTabs;
  _mFuncSym = func_like->getSymbol();

  std::stringstream orig_stream(std::move(mStr));
  mStr = std::stringstream();
  body->visit(this);
  std::string func_body_str {mStr.str()};
  mStr = std::move(orig_stream);

  mStr << _mFuncPreludeStr.str();
  mStr << func_body_str;

  _mFuncPreludeStr.str("");
  _mFuncPreludeStr.clear();
  mStr << '\n';
}

bool PythonVisitor::visit(LSLIntegerConstant *int_const) {
  // Usually you'd need an `S32()`, but we natively deal in int32 anyway.
  mStr << int_const->getValue();
  return false;
}

bool PythonVisitor::visit(LSLFloatConstant *float_const) {
  writeFloat(float_const->getValue());
  return false;
}

bool PythonVisitor::visit(LSLStringConstant *str_const) {
  // TODO: Probably not correctly accounting for encoding.
  mStr << '"' << escape_string(str_const->getValue()) << '"';
  return false;
}

bool PythonVisitor::visit(LSLKeyConstant *key_const) {
  // TODO: Probably not correctly accounting for encoding.
  mStr << "Key(\"" << escape_string(key_const->getValue()) << "\")";
  return false;
}

bool PythonVisitor::visit(LSLVectorConstant *vec_const) {
  auto *val = vec_const->getValue();
  mStr << "Vector((";
  writeFloat(val->x);
  mStr << ", ";
  writeFloat(val->y);
  mStr << ", ";
  writeFloat(val->z);
  mStr << "))";
  return false;
}

bool PythonVisitor::visit(LSLQuaternionConstant *quat_const) {
  auto *val = quat_const->getValue();
  mStr << "Quaternion((";
  writeFloat(val->x);
  mStr << ", ";
  writeFloat(val->y);
  mStr << ", ";
  writeFloat(val->z);
  mStr << ", ";
  writeFloat(val->s);
  mStr << "))";
  return false;
}

bool PythonVisitor::visit(LSLVectorExpression *vec_expr) {
  mStr << "Vector((";
  writeChildrenSep(vec_expr, ", ");
  mStr << "))";
  return false;
}

bool PythonVisitor::visit(LSLQuaternionExpression *quat_expr) {
  mStr << "Quaternion((";
  writeChildrenSep(quat_expr, ", ");
  mStr << "))";
  return false;
}

bool PythonVisitor::visit(LSLTypecastExpression *cast_expr) {
  auto *child_expr = cast_expr->getChildExpr();
  auto from_type = child_expr->getIType();
  auto to_type = cast_expr->getIType();
  if (from_type == LST_INTEGER && to_type == LST_FLOATINGPOINT) {
    // these are less annoying to read and basically the same thing
    if (child_expr->getNodeSubType() == NODE_CONSTANT_EXPRESSION) {
      // runtime cast makes this ugly and isn't necessary, just print it as a float literal.
      child_expr->visit(this);
      mStr << ".0";
    } else {
      mStr << "float(";
      child_expr->visit(this);
      mStr << ')';
    }
    return false;
  }
  mStr << "typecast(";
  child_expr->visit(this);
  mStr << ", " << PY_TYPE_NAMES[cast_expr->getIType()] << ")";
  return false;
}

bool PythonVisitor::visit(LSLListConstant *list_const) {
  mStr << '[';
  writeChildrenSep(list_const, ", ");
  mStr << ']';
  return false;
}

bool PythonVisitor::visit(LSLListExpression *list_expr) {
  mStr << '[';
  writeChildrenSep(list_expr, ", ");
  mStr << ']';
  return false;
}

bool PythonVisitor::visit(LSLFunctionExpression *func_expr) {
  auto *sym = func_expr->getSymbol();
  mStr << "await self.";
  if (sym->getSubType() == SYM_BUILTIN) {
    mStr << "builtin_funcs.";
  }
  mStr << getSymbolName(sym) << "(";
  for (auto *arg : *func_expr->getArguments()) {
    arg->visit(this);
    if (arg->getNext())
      mStr << ", ";
  }
  mStr << ')';
  return false;
}

static int member_to_offset(const char *member) {
  // Vector and Quaternion aren't namedtuples so we can't do the nice thing.
  int offset;
  switch(member[0]) {
    case 'x': offset = 0; break;
    case 'y': offset = 1; break;
    case 'z': offset = 2; break;
    case 's': offset = 3; break;
    default:
      offset = 0;
      assert(0);
  }
  return offset;
}

bool PythonVisitor::visit(LSLLValueExpression *lvalue) {
  if (lvalue->getSymbol()->getSubType() == SYM_GLOBAL)
    mStr << "self.";
  mStr << getSymbolName(lvalue->getSymbol());
  if (auto *member = lvalue->getMember()) {
    mStr << '[' << member_to_offset(member->getName()) << ']';
  }
  return false;
}

void PythonVisitor::constructMutatedMember(LSLSymbol *sym, LSLIdentifier *member, LSLExpression *rhs) {
  // Member case is special. We actually need to construct a new version of the same
  // type of object with only the selected member swapped out, and then assign _that_.
  int member_offset = member_to_offset(member->getName());
  mStr << "replace_coord_axis(";
  if (sym->getSubType() == SYM_GLOBAL)
    mStr << "self.";
  mStr << getSymbolName(sym) << ", " << member_offset << ", ";
  rhs->visit(this);
  mStr << ')';
}

bool PythonVisitor::visit(LSLBinaryExpression *bin_expr) {
  auto op = bin_expr->getOperation();
  auto *lhs = bin_expr->getLHS();
  auto *rhs = bin_expr->getRHS();

  if (op == '=') {
    auto *lvalue = (LSLLValueExpression *) lhs;
    auto *sym = lvalue->getSymbol();
    // If our result isn't needed, this expression will be put in a statement context in Python.
    // We can just directly assign, no special song and dance. There are some other cases where
    // we can do this but we'll worry about them later since they don't come up as often.
    if (!bin_expr->getResultNeeded()) {
      if (sym->getSubType() == SYM_GLOBAL)
        mStr << "self.";
      mStr << getSymbolName(sym) << " = ";
      if (auto *member = lvalue->getMember()) {
        constructMutatedMember(sym, member, rhs);
      } else {
        rhs->visit(this);
      }
    } else {
      if (sym->getSubType() == SYM_GLOBAL) {
        // walrus operator can't assign to these, need to use special assignment helper.
        mStr << "assign(self.__dict__, \"" << getSymbolName(sym) << "\", ";
      } else {
        // We need to wrap this assignment in parens so we can use the walrus operator.
        // walrus operator works regardless of expression or statement context, but doesn't
        // work for cases like `(self.foo := 2)` where we're assigning to an attribute rather than
        // just a single identifier...
        mStr << '(' << getSymbolName(sym) << " := ";
      }

      if (auto *member = lvalue->getMember()) {
        constructMutatedMember(sym, member, rhs);
      } else {
        rhs->visit(this);
      }
      mStr << ')';
      if (auto *member = lvalue->getMember()) {
        mStr << '[' << member_to_offset(member->getName()) << ']';
      }
    }
    return false;
  }
  if (op == OP_MUL_ASSIGN) {
    // int *= float case
    auto *sym = lhs->getSymbol();
    if (sym->getSubType() == SYM_GLOBAL) {
      // walrus operator can't assign to these, need to use special assignment helper.
      mStr << "assign(self.__dict__, \"" << getSymbolName(sym) << "\", ";
    } else {
      mStr << '(' << getSymbolName(sym) << " := ";
    }
    // don't have to consider the member case, no such thing as coordinates with int members.
    mStr << "typecast(rmul(";
    rhs->visit(this);
    mStr << ", ";
    lhs->visit(this);
    mStr << "), int))";
    return false;
  }
  switch(op) {
    case '+':            mStr << "radd("; break;
    case '-':            mStr << "rsub("; break;
    case '*':            mStr << "rmul("; break;
    case '/':            mStr << "rdiv("; break;
    case '%':            mStr << "rmod("; break;
    case OP_EQ:          mStr << "req("; break;
    case OP_NEQ:         mStr << "rneq("; break;
    case OP_GREATER:     mStr << "rgreater("; break;
    case OP_LESS:        mStr << "rless("; break;
    case OP_GEQ:         mStr << "rgeq("; break;
    case OP_LEQ:         mStr << "rleq("; break;
    case OP_BOOLEAN_AND: mStr << "rbooland("; break;
    case OP_BOOLEAN_OR:  mStr << "rboolor("; break;
    case OP_BIT_AND:     mStr << "rbitand("; break;
    case OP_BIT_OR:      mStr << "rbitor("; break;
    case OP_BIT_XOR:     mStr << "rbitxor("; break;
    case OP_SHIFT_LEFT:  mStr << "rshl("; break;
    case OP_SHIFT_RIGHT: mStr << "rshr("; break;
    default:
      assert(0);
      mStr << "<ERROR>";
  }
  rhs->visit(this);
  mStr << ", ";
  lhs->visit(this);
  mStr << ')';
  return false;
}

bool PythonVisitor::visit(LSLUnaryExpression *unary_expr) {
  auto *child_expr = unary_expr->getChildExpr();
  auto op = unary_expr->getOperation();
  if (op == OP_POST_DECR || op == OP_POST_INCR || op == OP_PRE_DECR || op == OP_PRE_INCR) {
    int post = op == OP_POST_INCR || op == OP_POST_DECR;
    int negative = op == OP_POST_DECR || op == OP_PRE_DECR;
    auto *lvalue = (LSLLValueExpression *) child_expr;
    auto *sym = lvalue->getSymbol();
    bool global = sym->getSubType() == SYM_GLOBAL;
    auto *member = lvalue->getMember();

    if (unary_expr->getResultNeeded() || member) {
      // this is in expression context, not statement context. We need to emulate the
      // side-effects of ++foo and foo++ in an expression, since that construct doesn't exist
      // in python.
      if (post)
        mStr << "post";
      else
        mStr << "pre";

      if (negative)
        mStr << "decr";
      else
        mStr << "incr";

      mStr << '(';
      if (global)
        mStr << "self.__dict__";
      else
        mStr << "locals()";
      mStr << ", \"" << getSymbolName(sym) << "\"";
      if (auto *member = lvalue->getMember()) {
        mStr << ", " << member_to_offset(member->getName());
      }
      mStr << ')';
    } else {
      // in statement context, we can use the more idiomatic foo += 1 or foo -= 1.
      if (sym->getSubType() == SYM_GLOBAL)
        mStr << "self.";
      mStr << getSymbolName(sym);
      if (op == OP_POST_DECR || op == OP_PRE_DECR) {
        mStr << " -= ";
      } else {
        mStr << " += ";
      }
      child_expr->getType()->getOneValue()->visit(this);
    }
    return false;
  }

  switch (op) {
    case '-': mStr << "neg("; break;
    case '~': mStr << "bitnot("; break;
    case '!': mStr << "boolnot("; break;
    default:
      assert(0);
      mStr << "<ERROR>";
  }
  child_expr->visit(this);
  mStr << ')';
  return false;
}

bool PythonVisitor::visit(LSLPrintExpression *print_expr) {
  mStr << "print(";
  print_expr->getChildExpr()->visit(this);
  mStr << ')';
  return false;
}

bool PythonVisitor::visit(LSLParenthesisExpression *parens_expr) {
  mStr << "(";
  parens_expr->getChildExpr()->visit(this);
  mStr << ')';
  return false;
}

bool PythonVisitor::visit(LSLBoolConversionExpression *bool_expr) {
  mStr << "cond(";
  bool_expr->getChildExpr()->visit(this);
  mStr << ")";
  return false;
}


bool PythonVisitor::visit(LSLNopStatement *nop_stmt) {
  doTabs();
  mStr << "pass\n";
  return false;
}

bool PythonVisitor::visit(LSLCompoundStatement *compound_stmt) {
  if (compound_stmt->hasChildren()) {
    visitChildren(compound_stmt);
  } else {
    doTabs();
    mStr << "pass\n";
  }
  return false;
}

bool PythonVisitor::visit(LSLExpressionStatement *expr_stmt) {
  doTabs();
  expr_stmt->getExpr()->visit(this);
  mStr << '\n';
  return false;
}

bool PythonVisitor::visit(LSLDeclaration *decl_stmt) {
  doTabs();
  auto *sym = decl_stmt->getSymbol();

  if (_mFuncSym->getHasUnstructuredJumps()) {
    // get down to our nasty declaration hoisting business.
    // the declaration will be added to the prelude stringstream
    for(int i=0; i<_mFuncPreludeTabs; ++i) {
      _mFuncPreludeStr << "    ";
    }
    // We need a "pre-initialization" to handle the weirdness that comes with jumping over declarations
    // some variables have different values before they're initialized by the declaration statement!
    // this is only an issue if we have unstructured jumps, which could have jumped over a declaration
    // node that would have done an assignment. No unstructured jumps means no use-before-initialization
    // means no need to hoist. At least as of CPython 3.11 beta, these "unnecessary" declarations aren't
    // eliminated by the peepholer.
    _mFuncPreludeStr << getSymbolName(sym) << ": " << PY_PRELUDE_TYPE_NAMES[sym->getIType()] << " = ";
    switch(sym->getIType()) {
      case LST_INTEGER:
        _mFuncPreludeStr << "0";
        break;
      case LST_FLOATINGPOINT:
        _mFuncPreludeStr << "0.0";
        break;
      case LST_STRING:
      case LST_KEY:
      case LST_LIST:
        _mFuncPreludeStr << "None";
        break;
      case LST_VECTOR:
        _mFuncPreludeStr << "Vector((0.0, 0.0, 0.0))";
        break;
      case LST_QUATERNION:
        // NOT 0.0, 0.0, 0.0, 1.0!
        _mFuncPreludeStr << "Quaternion((0.0, 0.0, 0.0, 0.0))";
        break;
      default:
        assert(0);
    }
    _mFuncPreludeStr << '\n';

    // now handle the assignment at the actual declaration node
    mStr << getSymbolName(sym) << " = ";
  } else {
    // don't need hoisting, do the declaration inline
    mStr << getSymbolName(sym) << ": " << PY_TYPE_NAMES[sym->getIType()] << " = ";
  }

  LSLASTNode *initializer = decl_stmt->getInitializer();
  if (!initializer) {
    initializer = sym->getType()->getDefaultValue();
  }
  initializer->visit(this);
  mStr << "\n";
  return false;
}

bool PythonVisitor::visit(LSLIfStatement *if_stmt) {
  doTabs();
  mStr << "if ";
  if_stmt->getCheckExpr()->visit(this);
  mStr << ":\n";
  {
    ScopedTabSetter tab_setter(this, mTabs + 1);
    if_stmt->getTrueBranch()->visit(this);
  }

  if(auto *false_branch = if_stmt->getFalseBranch()) {
    doTabs();
    bool chained_if = false_branch->getNodeSubType() == NODE_IF_STATEMENT;
    if (chained_if) {
      mStr << "el";
      // make the "if" branch's "if" merge into an "elif", no leading tab!
      mSuppressNextTab = true;
    } else {
      mStr << "else:\n";
    }

    ScopedTabSetter tab_setter(this, mTabs + (chained_if ? 0 : 1));
    false_branch->visit(this);
  }
  return false;
}

bool PythonVisitor::visit(LSLForStatement *for_stmt) {
  // initializer expressions come as ExpressionStatements before the actual loop
  for (auto *init_expr : *for_stmt->getInitExprs()) {
    doTabs();
    init_expr->visit(this);
    mStr << '\n';
  }
  // all loops are represented as `while`s in Python for consistency
  // since LSL's loop semantics are different from Python's
  doTabs();
  // The `True == True` is to force pessimization of Python's dead code eliminator,
  // otherwise it can turn the loop into an unconditional jump with everything after
  // the loop eliminated, not aware of the `goto` semantics we've added in for jumps.
  mStr << "while True == True:\n";
  {
    ScopedTabSetter tab_setter_1(this, mTabs + 1);

    doTabs();
    mStr << "if not ";
    for_stmt->getCheckExpr()->visit(this);
    mStr << ":\n";
    {
      ScopedTabSetter tab_setter_2(this, mTabs + 1);
      doTabs();
      mStr << "break\n";
    }

    for_stmt->getBody()->visit(this);
    for (auto *incr_expr : *for_stmt->getIncrExprs()) {
      doTabs();
      incr_expr->visit(this);
      mStr << '\n';
    }
  }
  return false;
}

bool PythonVisitor::visit(LSLWhileStatement *while_stmt) {
  doTabs();
  mStr << "while ";
  while_stmt->getCheckExpr()->visit(this);
  mStr << ":\n";
  {
    ScopedTabSetter tab_setter_1(this, mTabs + 1);
    while_stmt->getBody()->visit(this);
  }
  return false;
}

bool PythonVisitor::visit(LSLDoStatement *do_stmt) {
  doTabs();
  mStr << "while True == True:\n";
  {
    ScopedTabSetter tab_setter_1(this, mTabs + 1);
    do_stmt->getBody()->visit(this);
    doTabs();
    mStr << "if not ";
    do_stmt->getCheckExpr()->visit(this);
    mStr << ":\n";
    {
      ScopedTabSetter tab_setter_2(this, mTabs + 1);
      doTabs();
      mStr << "break\n";
    }
  }
  return false;
}

bool PythonVisitor::visit(LSLJumpStatement *jump_stmt) {
  doTabs();
  // We could check `continueLike` or `breakLike` here, but
  // LSL's `for` semantics differ from Python's, so we'd have to use
  // an exception in the `for` case anyways. No sense in pretending
  // we have structured jumps when we really don't, I guess.
  mStr << "goto ." << getSymbolName(jump_stmt->getSymbol()) << "\n";
  return false;
}

bool PythonVisitor::visit(LSLLabel *label_stmt) {
  doTabs();
  mStr << "label ." << getSymbolName(label_stmt->getSymbol()) << "\n";
  return false;
}

bool PythonVisitor::visit(LSLReturnStatement *return_stmt) {
  if (_mFuncSym->getHasJumps()) {
    // we need to do extra work to make sure code past this return doesn't get eliminated
    // by Python's dead code eliminator. Putting the return in a conditional branch that
    // the compiler doesn't reason about statically is sufficient for that.
    // necessary even with only "structured" jumps because we can't actually use the `continue`
    // keyword due to differing looping constructs between Python and LSL.
    // Technically there are ways we could represent loops that would allows us to use the
    // `continue` keyword, but they'd be much, much uglier than this dumb little hack.
    doTabs();
    mStr << "if True == True:\n";
    ScopedTabSetter tab_setter(this, mTabs + 1);
    writeReturn(return_stmt->getExpr());
  } else {
    writeReturn(return_stmt->getExpr());
  }
  return false;
}

void PythonVisitor::writeReturn(LSLExpression *ret_expr) {
  doTabs();
  if (ret_expr) {
    mStr << "return ";
    ret_expr->visit(this);
  } else {
    mStr << "return";
  }
  mStr << '\n';
}

bool PythonVisitor::visit(LSLStateStatement *state_stmt) {
  doTabs();
  mStr << "raise StateChangeException('" << getSymbolName(state_stmt->getSymbol()) << "')\n";
  return false;
}
