#include <tailslide/visitor.hh>
#include <tailslide/passes/desugaring.hh>
#include "json_ir_pass.hh"

namespace Tailslide {

using json = nlohmann::json;


bool JSONResourceVisitor::visit(LSLGlobalFunction *glob_func) {
  auto *sym = glob_func->getSymbol();
  auto *func_sym_data = getSymbolData(sym);
  _mCurrentFunc = func_sym_data;
  // pick up local declarations
  handleFuncDecl(glob_func->getArguments());
  visitChildren(glob_func);
  _mCurrentFunc = nullptr;
  return false;
}

bool JSONResourceVisitor::visit(LSLEventHandler *handler) {
  auto *sym = handler->getSymbol();
  auto *handler_sym_data = getSymbolData(sym);
  _mCurrentFunc = handler_sym_data;
  // pick up local declarations
  handleFuncDecl(handler->getArguments());
  visitChildren(handler);
  _mCurrentFunc = nullptr;
  return false;
}

void JSONResourceVisitor::handleFuncDecl(LSLASTNode *func_decl) {
  if (!func_decl || !func_decl->hasChildren())
    return;
  for (auto *param : *func_decl) {
    auto *param_sym = param->getSymbol();
    auto *param_sym_data = getSymbolData(param_sym);
    param_sym_data->index = _mCurrentFunc->args.size();
    _mCurrentFunc->args.push_back(param->getIType());
  }
}

bool JSONResourceVisitor::visit(LSLDeclaration *decl_stmt) {
  auto *sym = decl_stmt->getSymbol();
  auto *sym_data = getSymbolData(sym);
  sym_data->index = (uint32_t)_mCurrentFunc->locals.size();
  _mCurrentFunc->locals.push_back(sym->getIType());
  return true;
}

bool JSONResourceVisitor::visit(LSLGlobalVariable *global_var) {
  auto *sym = global_var->getSymbol();
  auto *sym_data = getSymbolData(sym);
  sym_data->index = _mGlobals++;
  return true;
}

JSONSymbolData *JSONResourceVisitor::getSymbolData(LSLSymbol *sym) {
  auto sym_iter = _mSymData->find(sym);
  if (sym_iter != _mSymData->end())
    return &sym_iter->second;
  (*_mSymData)[sym] = {};
  return &_mSymData->find(sym)->second;
}


bool JSONScriptCompiler::visit(LSLScript *script) {
  DeSugaringVisitor de_sugaring_visitor(_mAllocator, true);
  script->visit(&de_sugaring_visitor);

  JSONResourceVisitor resource_visitor(&_mSymData);
  script->visit(&resource_visitor);

  auto *globals = script->getGlobals();

  // declare the global variables first
  json::array_t global_types;
  for (auto *global: *globals) {
    if (global->getNodeType() != NODE_GLOBAL_VARIABLE)
      continue;
    global_types.push_back(JSON_TYPE_NAMES[global->getSymbol()->getIType()]);
  }
  mIR["globals"] = global_types;

  // Now build up the code needed to initialize the globals
  _mCode.clear();
  for (auto *global: *globals) {
    if (global->getNodeType() != NODE_GLOBAL_VARIABLE)
      continue;
    global->visit(this);
  }
  // "init_code" is implemented as a function, it needs a ret!
  writeOp({
      {"op", "RET"}
  });
  mIR["init_code"] = _mCode;

  // then handle functions
  json::array_t global_funcs;
  for (auto *global: *globals) {
    if (global->getNodeType() != NODE_GLOBAL_FUNCTION)
      continue;
    global->visit(this);
    global_funcs.push_back(_mFunction);
  }
  mIR["functions"] = global_funcs;

  // then event handlers for states
  json::array_t states;
  for (auto *state: *script->getStates()) {
    json::array_t handlers;
    for (auto *handler : *((LSLState *)state)->getEventHandlers()) {
      _mFunction.clear();
      handler->visit(this);
      handlers.push_back(_mFunction);
    }
    states.push_back({
        {"name", state->getSymbol()->getName()},
        {"handlers", handlers}
    });
  }
  mIR["states"] = states;

  return false;
}

void JSONScriptCompiler::writeOp(nlohmann::json::object_t op_data) {
  op_data["instr_type"] = "op";
  _mCode.push_back(op_data);
}

void JSONScriptCompiler::writeJump(const std::string &label, const std::string &jump_type) {
  writeOp({
      {"op", "JUMP"},
      {"jump_type", jump_type},
      {"label", label}
  });
}

void JSONScriptCompiler::writeLabel(const std::string &label) {
  _mCode.push_back({
      {"instr_type", "label"},
      {"label", label}
  });
}

void JSONScriptCompiler::writePop(uint32_t num_pops) {
  writeOp({
      {"op", "POP_N"},
      {"num", num_pops}
  });
}

static std::string sym_to_whence(LSLSymbol *sym) {
  switch(sym->getSubType()) {
    case SYM_GLOBAL:
      return "GLOBAL";
    case SYM_LOCAL:
      return "LOCAL";
    case SYM_EVENT_PARAMETER:
    case SYM_FUNCTION_PARAMETER:
      return "ARG";
    default:
      assert(0);
      return "";
  }
}

bool JSONScriptCompiler::visit(LSLGlobalVariable *glob_var) {
  // we only care about the case where there's an initializer.
  // if there's no initializer we rely on the default value already
  // having been set.
  auto *sym = glob_var->getSymbol();
  if (auto *initializer = glob_var->getInitializer()) {
    initializer->visit(this);
    writeOp({
      {"op", "STORE"},
      {"type", JSON_TYPE_NAMES[sym->getIType()]},
      {"whence", sym_to_whence(sym)},
      {"index", _mSymData[sym].index}
    });
  }
  return false;
}

bool JSONScriptCompiler::visit(LSLDeclaration *decl_stmt) {
  auto *sym = decl_stmt->getSymbol();
  json::object_t push_instr({
      {"op", "STORE"},
      {"type", JSON_TYPE_NAMES[sym->getIType()]},
      {"whence", sym_to_whence(sym)},
      {"index", _mSymData[sym].index}
  });

  if (auto *initializer = decl_stmt->getInitializer()) {
    // need to run the RHS expression before we can store
    initializer->visit(this);
  } else {
    // even if nothing is specified we _have_ to store something, otherwise
    // variables in loops won't have their values correctly reset. STORE_DEFAULT
    // is a special case that doesn't require
    push_instr["op"] = "STORE_DEFAULT";
  }
  writeOp(push_instr);
  return false;
}


bool JSONScriptCompiler::visit(LSLIfStatement *if_stmt) {
  auto jump_past_true_label = "LabelTempJump" + std::to_string(_mJumpNum++);
  std::string jump_past_false_label;
  auto *false_node = if_stmt->getFalseBranch();
  if (false_node)
    jump_past_false_label = "LabelTempJump" + std::to_string(_mJumpNum++);

  if_stmt->getCheckExpr()->visit(this);
  writeJump(jump_past_true_label, "NIF");
  if_stmt->getTrueBranch()->visit(this);
  if (false_node) {
    writeJump(jump_past_false_label, "ALWAYS");
    writeLabel(jump_past_true_label);
    false_node->visit(this);
    writeLabel(jump_past_false_label);
  } else {
    writeLabel(jump_past_true_label);
  }
  return false;
}

bool JSONScriptCompiler::visit(LSLForStatement *for_stmt) {
  // execute instructions to initialize vars
  for(auto *init_expr : *for_stmt->getInitExprs()) {
    init_expr->visit(this);
    if (init_expr->getIType() && !_mPushOmitted)
      writePop(1);
    _mPushOmitted = false;
  }
  auto jump_to_start_label = "LabelTempJump" + std::to_string(_mJumpNum++);
  auto jump_to_end_label = "LabelTempJump" + std::to_string(_mJumpNum++);
  writeLabel(jump_to_start_label);
  // run the check expression, exiting the loop if it fails
  for_stmt->getCheckExpr()->visit(this);
  writeJump(jump_to_end_label, "NIF");
  // run the body of the loop
  for_stmt->getBody()->visit(this);
  // run the increment expressions
  for(auto *incr_expr : *for_stmt->getIncrExprs()) {
    incr_expr->visit(this);
    if (incr_expr->getIType() && !_mPushOmitted)
      writePop(1);
    _mPushOmitted = false;
  }
  // jump back up to the check expression at the top
  writeJump(jump_to_start_label, "ALWAYS");
  writeLabel(jump_to_end_label);
  return false;
}

bool JSONScriptCompiler::visit(LSLWhileStatement* while_stmt) {
  auto jump_to_start_label = "LabelTempJump" + std::to_string(_mJumpNum++);
  auto jump_to_end_label = "LabelTempJump" + std::to_string(_mJumpNum++);
  writeLabel(jump_to_start_label);
  // run the check expression, exiting the loop if it fails
  while_stmt->getCheckExpr()->visit(this);
  writeJump(jump_to_end_label, "NIF");
  // run the body of the loop
  while_stmt->getBody()->visit(this);
  // jump back up to the check expression at the top
  writeJump(jump_to_start_label, "ALWAYS");
  writeLabel(jump_to_end_label);
  return false;
}

bool JSONScriptCompiler::visit(LSLDoStatement* do_stmt) {
  auto jump_to_start_label = "LabelTempJump" + std::to_string(_mJumpNum++);
  writeLabel(jump_to_start_label);
  // run the body of the loop
  do_stmt->getBody()->visit(this);
  // run the check expression, jumping back up if it succeeds
  do_stmt->getCheckExpr()->visit(this);
  writeJump(jump_to_start_label, "IF");
  return false;
}

bool JSONScriptCompiler::visit(LSLStateStatement *state_stmt) {
  writeOp({
      {"op", "CHANGE_STATE"},
      {"state", state_stmt->getSymbol()->getName()}
  });
  return false;
}

bool JSONScriptCompiler::visit(LSLExpressionStatement *expr_stmt) {
  auto *expr = expr_stmt->getExpr();
  expr->visit(this);
  if (expr->getIType() && !_mPushOmitted) {
    writePop(1);
  }
  _mPushOmitted = false;
  return false;
}

bool JSONScriptCompiler::visit(LSLReturnStatement *ret_stmt) {
  if (auto *expr = ret_stmt->getExpr()) {
    expr->visit(this);
    if (expr->getIType()) {
      writeOp({
          {"op", "STORE"},
          {"type", JSON_TYPE_NAMES[expr->getIType()]},
          // only real in IR, would actually store to "ARG", num_args in assembly
          {"whence", "RETURN"},
          {"index", 0}
      });
    }
  }
  // ret is responsible for popping args, IR->Assembly converted populates
  // the argument num, not us!
  writeOp({
      {"op", "RET"}
  });
  return false;
}

bool JSONScriptCompiler::visit(LSLLabel *label_stmt) {
  // TODO: right now this roughly matches LL's behavior, but label names
  //  should be mangled to prevent collisions.
  writeLabel(label_stmt->getSymbol()->getName());
  return false;
}

bool JSONScriptCompiler::visit(LSLJumpStatement *jump_stmt) {
  // TODO: right now this roughly matches LL's behavior, but label names
  //  should be mangled to prevent collisions.
  // note that labels are scoped to a specific function in our IR
  writeJump(jump_stmt->getSymbol()->getName(), "ALWAYS");
  return false;
}

/// push the actual value of an lvalue onto the stack
void JSONScriptCompiler::pushLValue(LSLLValueExpression *lvalue) {
  auto *sym = lvalue->getSymbol();
  writeOp({
      {"op", "PUSH"},
      {"type", JSON_TYPE_NAMES[sym->getIType()]},
      {"whence", sym_to_whence(sym)},
      {"index", _mSymData[sym].index}
  });

  if (auto *member = lvalue->getMember()) {
    // accessor case, containing object is already on the stack and
    // we just have to load the field.
    uint32_t member_idx = 0;
    switch(member->getName()[0]) {
      case 'x': member_idx = 0; break;
      case 'y': member_idx = 1; break;
      case 'z': member_idx = 2; break;
      case 's': member_idx = 3; break;
    }
    writeOp({
        {"op", "TAKE_MEMBER"},
        {"type", JSON_TYPE_NAMES[sym->getIType()]},
        {"offset", member_idx}
    });
  }
}

static json float_to_json(float f_val) {
  // JSON can't actually represent inf or nan, need to stringify :/
  if (!std::isfinite(f_val)) {
    if (f_val > 0.0f)
      return json::string_t{"inf"};
    else if (f_val < 0.0f)
      return json::string_t{"-inf"};
    else
      return json::string_t{"nan"};
  }
  return json::number_float_t{f_val};
}

void JSONScriptCompiler::pushConstant(LSLConstant *cv) {
  if (!cv)
    return;

  json::object_t obj {
      {"op", "PUSH_CONSTANT"},
      {"type", JSON_TYPE_NAMES[cv->getIType()]}
  };
  switch(cv->getIType()) {
    case LST_INTEGER:
      obj["value"] = ((LSLIntegerConstant *) cv)->getValue();
      break;
    case LST_FLOATINGPOINT: {
      obj["value"] = float_to_json(((LSLFloatConstant *) cv)->getValue());
      break;
    }
    case LST_STRING:
      obj["value"] = ((LSLStringConstant *) cv)->getValue();
      break;
    case LST_KEY:
      obj["value"] = ((LSLKeyConstant *) cv)->getValue();
      break;
    case LST_VECTOR: {
      json::array_t coord_array;
      auto *vec_val = ((LSLVectorConstant *) cv)->getValue();
      coord_array.push_back(float_to_json(vec_val->x));
      coord_array.push_back(float_to_json(vec_val->y));
      coord_array.push_back(float_to_json(vec_val->z));
      obj["value"] = coord_array;
      break;
    }
    case LST_QUATERNION: {
      json::array_t coord_array;
      auto *vec_val = ((LSLQuaternionConstant *) cv)->getValue();
      coord_array.push_back(float_to_json(vec_val->x));
      coord_array.push_back(float_to_json(vec_val->y));
      coord_array.push_back(float_to_json(vec_val->z));
      coord_array.push_back(float_to_json(vec_val->s));
      obj["value"] = coord_array;
      break;
    }
    case LST_LIST: {
      // only know how to write the default empty list as a constant
      auto *list_val = (LSLListConstant *) cv;
      assert(!list_val->getLength());
      obj["value"] = json::array();
      break;
    }
    default:
      assert(0);
  }

  writeOp(obj);
}

void JSONScriptCompiler::storeToLValue(LSLLValueExpression *lvalue, bool push_result) {
  auto *sym = lvalue->getSymbol();
  // We can avoid reloading the lvalue from its storage container in these cases by just duplicating
  // the result of the expression on the stack. All we need on the stack for these stores is the value.
  if (push_result) {
    writeOp({{"op", "DUP"}});
  }

  if (auto *member = lvalue->getMember()) {
    // accessor case, need to load containing object to replace the member
    writeOp({
        {"op", "PUSH"},
        {"type", JSON_TYPE_NAMES[sym->getIType()]},
        {"whence", sym_to_whence(sym)},
        {"index", _mSymData[sym].index}
    });

    uint32_t member_idx = 0;
    switch(member->getName()[0]) {
      case 'x': member_idx = 0; break;
      case 'y': member_idx = 1; break;
      case 'z': member_idx = 2; break;
      case 's': member_idx = 3; break;
    }
    writeOp({
        {"op", "REPLACE_MEMBER"},
        {"type", JSON_TYPE_NAMES[sym->getIType()]},
        {"offset", member_idx}
    });
  }

  writeOp({
      {"op", "STORE"},
      {"type", JSON_TYPE_NAMES[sym->getIType()]},
      {"whence", sym_to_whence(sym)},
      {"index", _mSymData[sym].index}
  });
}

bool JSONScriptCompiler::visit(LSLGlobalFunction *glob_func) {
  buildFunction(glob_func);
  return false;
}

bool JSONScriptCompiler::visit(LSLEventHandler *glob_func) {
  buildFunction(glob_func);
  return false;
}

void JSONScriptCompiler::buildFunction(LSLASTNode *func) {
  // write out the parameter list
  auto *func_sym = func->getSymbol();
  auto *func_decl = func_sym->getFunctionDecl();

  _mFunction["name"] = func_sym->getName();
  _mFunction["return"] = JSON_TYPE_NAMES[func_sym->getIType()];

  json::array_t args;
  for (auto *func_param : *func_decl) {
    args.push_back(JSON_TYPE_NAMES[func_param->getIType()]);
  }
  _mFunction["args"] = args;

  json::array_t locals;
  for (auto param_type : _mSymData[func_sym].locals) {
    locals.push_back(JSON_TYPE_NAMES[param_type]);
  }
  _mFunction["locals"] = locals;

  _mCode.clear();
  visitChildren(func);
  if (!func_sym->getAllPathsReturn())
    writeOp({{"op", "RET"}});
  _mFunction["code"] = _mCode;
}

bool JSONScriptCompiler::visit(LSLConstantExpression *constant_expr) {
  pushConstant(constant_expr->getConstantValue());
  return false;
}

bool JSONScriptCompiler::visit(LSLTypecastExpression *cast_expr) {
  cast_expr->getChildExpr()->visit(this);
  // this is a no-op cast, don't emit anything.
  if (cast_expr->getIType() == cast_expr->getChildExpr()->getIType())
    return false;

  writeOp({
      {"op", "CAST"},
      {"from_type", JSON_TYPE_NAMES[cast_expr->getChildExpr()->getIType()]},
      {"to_type", JSON_TYPE_NAMES[cast_expr->getIType()]}
  });
  return false;
}

bool JSONScriptCompiler::visit(LSLBoolConversionExpression *bool_expr) {
  bool_expr->getChildExpr()->visit(this);
  writeOp({
      {"op", "BOOL"},
      {"type", JSON_TYPE_NAMES[bool_expr->getChildExpr()->getIType()]}
  });
  return false;
}

bool JSONScriptCompiler::visit(LSLVectorExpression *vec_expr) {
  visitChildren(vec_expr);
  pushCoordinate(LST_VECTOR);
  return false;
}

bool JSONScriptCompiler::visit(LSLQuaternionExpression *quat_expr) {
  visitChildren(quat_expr);
  pushCoordinate(LST_QUATERNION);
  return false;
}

void JSONScriptCompiler::pushCoordinate(Tailslide::LSLIType coord_type) {
  writeOp({
      {"op", "BUILD_COORD"},
      {"type", JSON_TYPE_NAMES[coord_type]}
  });
}

bool JSONScriptCompiler::visit(LSLLValueExpression *lvalue) {
  pushLValue(lvalue);
  return false;
}

bool JSONScriptCompiler::visit(LSLListExpression *list_expr) {
  uint32_t num_elems = 0;
  for (auto child : *list_expr) {
    child->visit(this);
    ++num_elems;
  }
  writeOp({
      {"op", "BUILD_LIST"},
      {"num_elems", num_elems}
  });
  return false;
}

bool JSONScriptCompiler::visit(LSLFunctionExpression *func_expr) {
  auto *func_sym = func_expr->getSymbol();
  // need to make a space above the arguments for the function to place
  // the return value. Library calls place the retval themselves where necessary.
  if (func_sym->getSubType() != SYM_BUILTIN && func_sym->getIType())
    writeOp({
        {"op", "PUSH_EMPTY"},
        {"type", JSON_TYPE_NAMES[func_sym->getIType()]}
    });

  // push the arguments onto the stack
  for (auto *child_expr : *func_expr->getArguments()) {
    child_expr->visit(this);
  }

  if (func_sym->getSubType() == SYM_BUILTIN) {
    writeOp({
        {"op", "CALL_LIB"},
        {"name", func_sym->getName()}
    });
  } else {
    writeOp({
        {"op", "CALL"},
        {"name", func_sym->getName()}
    });
  }
  return false;
}

static std::string operation_to_json_operation(LSLOperator operation) {
  switch (operation) {
    case '+': return "PLUS";
    case '-': return "MINUS";
    case '*': return "MUL";
    case '/': return "DIV";
    case '%': return "MOD";
    case OP_BOOLEAN_NOT: return "BOOLEAN_NOT";
    case OP_BOOLEAN_AND: return "BOOLEAN_AND";
    case OP_BOOLEAN_OR: return "BOOLEAN_OR";
    case OP_LESS: return "LESS";
    case OP_GREATER: return "GREATER";
    case OP_LEQ: return "LEQ";
    case OP_GEQ: return "GEQ";
    case OP_EQ: return "EQ";
    case OP_NEQ: return "NEQ";
    case OP_BIT_NOT: return "BIT_NOT";
    case OP_BIT_XOR: return "BIT_XOR";
    case OP_BIT_AND: return "BIT_AND";
    case OP_BIT_OR: return "BIT_OR";
    case OP_SHIFT_LEFT: return "SHIFT_LEFT";
    case OP_SHIFT_RIGHT: return "SHIFT_RIGHT";
    default: assert(0);
  }
  return "<INVALID>";
}

bool JSONScriptCompiler::visit(LSLBinaryExpression *bin_expr) {
  LSLOperator op = bin_expr->getOperation();
  auto *left = bin_expr->getLHS();
  auto *right = bin_expr->getRHS();

  if (op == '=') {
    right->visit(this);
    // store to the lvalue and push the lvalue back onto the stack
    // if we're assigning in an expression context. For something in
    // an expressionstatement context like `foo = 1` we omit the push.
    storeToLValue((LSLLValueExpression *) left, maybeOmitPush(bin_expr));
    return false;
  } else if (op == OP_MUL_ASSIGN) {
    // The only expression that gets left as a MUL_ASSIGN is the busted `int *= float` case,
    // all others get desugared to `lvalue = lvalue * rhs` in an earlier compile pass.
    // That expression is busted and not the same as `int = int * float`, obviously,
    // but we need to support it.
    right->visit(this);
    left->visit(this);
    // cast the integer lvalue to a float first
    writeOp({
        {"op", "CAST"},
        {"from_type", JSON_TYPE_NAMES[LST_INTEGER]},
        {"to_type", JSON_TYPE_NAMES[LST_FLOATINGPOINT]}
    });
    writeOp({
        {"op", "BIN_OP"},
        {"left_type", JSON_TYPE_NAMES[LST_FLOATINGPOINT]},
        {"right_type", JSON_TYPE_NAMES[LST_FLOATINGPOINT]},
        {"operation", "MUL"}
    });
    // cast the result to an integer so we can store it in the lvalue
    writeOp({
        {"op", "CAST"},
        {"from_type", JSON_TYPE_NAMES[LST_FLOATINGPOINT]},
        {"to_type", JSON_TYPE_NAMES[LST_INTEGER]}
    });
    // This will return the wrong type because things expect this expression to return a float.
    // Use of the retval will probably cause a crash.
    storeToLValue((LSLLValueExpression *)left, maybeOmitPush(bin_expr));
    return false;
  }

  right->visit(this);
  left->visit(this);
  writeOp({
      {"op", "BIN_OP"},
      {"left_type", JSON_TYPE_NAMES[left->getIType()]},
      {"right_type", JSON_TYPE_NAMES[right->getIType()]},
      {"operation", operation_to_json_operation(bin_expr->getOperation())}
  });

  return false;
}

bool JSONScriptCompiler::visit(LSLUnaryExpression *unary_expr) {
  auto *child_expr = unary_expr->getChildExpr();
  LSLOperator op = unary_expr->getOperation();

  if (op == OP_POST_DECR || op == OP_POST_INCR) {
    auto *lvalue = (LSLLValueExpression *) child_expr;

    // We need to keep the original value of the expression on the stack,
    // but only if the result of the expr will actually be used
    if (maybeOmitPush(unary_expr))
      pushLValue(lvalue);

    // push "one" for the given type
    pushConstant(lvalue->getType()->getOneValue());

    // Push the value onto the stack
    pushLValue(lvalue);

    LSLOperator underlying_op = OP_PLUS;
    if (op == OP_POST_DECR)
      underlying_op = OP_MINUS;
    writeOp({
        {"op", "BIN_OP"},
        {"left_type", JSON_TYPE_NAMES[child_expr->getIType()]},
        {"right_type", JSON_TYPE_NAMES[child_expr->getIType()]},
        {"operation", operation_to_json_operation(underlying_op)}
    });

    // This store + push, then subsequent pop is totally unnecessary, but matches what LL's
    //  compiler does. Only do it if we're not allowed to omit pushes.
    if (_mOptions.omit_unnecessary_pushes) {
      storeToLValue(lvalue, false);
    } else {
      storeToLValue(lvalue, true);
      writePop(1);
    }

    return false;
  } else if (op == OP_PRE_INCR || op == OP_PRE_DECR) {
    // This appears to generate different code from `lvalue = lvalue + 1`,
    // so it isn't desugared.
    auto *lvalue = (LSLLValueExpression *) child_expr;
    pushConstant(lvalue->getType()->getOneValue());
    pushLValue(lvalue);

    LSLOperator underlying_op = OP_PLUS;
    if (op == OP_PRE_DECR)
      underlying_op = OP_MINUS;
    writeOp({
        {"op", "BIN_OP"},
        {"left_type", JSON_TYPE_NAMES[child_expr->getIType()]},
        {"right_type", JSON_TYPE_NAMES[child_expr->getIType()]},
        {"operation", operation_to_json_operation(underlying_op)}
    });

    storeToLValue(lvalue, maybeOmitPush(unary_expr));
    return false;
  }

  child_expr->visit(this);
  writeOp({
      {"op", "UN_OP"},
      {"type", JSON_TYPE_NAMES[child_expr->getIType()]},
      {"operation", operation_to_json_operation(unary_expr->getOperation())}
  });
  return false;
}

bool JSONScriptCompiler::visit(LSLPrintExpression *print_expr) {
  print_expr->getChildExpr()->visit(this);
  writeOp({{"op", "DUMP"}});
  return false;
}

}
