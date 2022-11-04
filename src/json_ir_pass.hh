#pragma once

#include <vector>

#include <tailslide/tailslide.hh>
#include "../extern/json.hh"

namespace Tailslide {


struct JSONSymbolData {
  // Index of the given variable within its respective lookup table
  uint32_t index = 0;
  // all locals (if this symbol is a function or event handler)
  std::vector<LSLIType> locals{};
  // all arguments (if this symbol is a function or event handler)
  std::vector<LSLIType> args{};
};

typedef std::map<Tailslide::LSLSymbol *, JSONSymbolData> JSONSymbolDataMap;

// Walks the script, figuring out how much space to reserve for data slots
// and what order to place them in.
class JSONResourceVisitor : public ASTVisitor {
  public:
  explicit JSONResourceVisitor(JSONSymbolDataMap *sym_data) : _mSymData(sym_data) {}

  protected:
  bool visit(Tailslide::LSLGlobalFunction *glob_func) override;
  bool visit(Tailslide::LSLEventHandler *handler) override;
  bool visit(Tailslide::LSLDeclaration *decl_stmt) override;
  bool visit(Tailslide::LSLGlobalVariable *global_var) override;
  // not relevant
  bool visit(Tailslide::LSLExpression *expr) override { return false; };
  void handleFuncDecl(LSLASTNode *func_decl);

  JSONSymbolData *getSymbolData(Tailslide::LSLSymbol *sym);

  JSONSymbolData *_mCurrentFunc = nullptr;
  JSONSymbolDataMap *_mSymData = nullptr;
  uint32_t _mGlobals = 0;
};

struct JSONCompilationOptions {
  bool omit_unnecessary_pushes = false;
};

class JSONScriptCompiler : public ASTVisitor {
  public:
    explicit JSONScriptCompiler(ScriptAllocator *allocator, JSONCompilationOptions options={}) :
        _mAllocator(allocator), _mOptions(options) {};

    nlohmann::json mIR;
  protected:
    virtual bool visit(LSLScript *script);
    virtual bool visit(LSLGlobalVariable *glob_var);

    void writeOp(nlohmann::json::object_t op_data);
    void writeLabel(const std::string &label);
    void writeJump(const std::string &label, const std::string &jump_type);
    void writePop(uint32_t num_pops);
    void pushLValue(LSLLValueExpression *lvalue);
    void pushConstant(LSLConstant *cv);
    void storeToLValue(LSLLValueExpression *lvalue, bool push_result);

    virtual bool visit(LSLEventHandler *handler);
    virtual bool visit(LSLGlobalFunction *glob_func);
    void buildFunction(LSLASTNode *func);

    virtual bool visit(LSLExpressionStatement *expr_stmt);
    virtual bool visit(LSLReturnStatement *ret_stmt);
    virtual bool visit(LSLLabel *label_stmt);
    virtual bool visit(LSLJumpStatement *jump_stmt);
    virtual bool visit(LSLDeclaration *decl_stmt);
    virtual bool visit(LSLIfStatement *if_stmt);
    virtual bool visit(LSLForStatement *for_stmt);
    virtual bool visit(LSLWhileStatement *while_stmt);
    virtual bool visit(LSLDoStatement *do_stmt);
    virtual bool visit(LSLStateStatement *state_stmt);

    virtual bool visit(LSLConstantExpression *constant_expr);
    virtual bool visit(LSLTypecastExpression *cast_expr);
    virtual bool visit(LSLBoolConversionExpression *bool_expr);
    virtual bool visit(LSLVectorExpression *vec_expr);
    virtual bool visit(LSLQuaternionExpression *quat_expr);
    void pushCoordinate(LSLIType coord_type);
    virtual bool visit(LSLLValueExpression *lvalue);
    virtual bool visit(LSLListExpression *list_expr);
    virtual bool visit(LSLFunctionExpression *func_expr);
    virtual bool visit(LSLBinaryExpression *bin_expr);
    virtual bool visit(LSLUnaryExpression *unary_expr);
    virtual bool visit(LSLPrintExpression *print_expr);

    bool maybeOmitPush(LSLExpression *expr) {
        bool need_push = !_mOptions.omit_unnecessary_pushes || expr->getResultNeeded();
        // tell our parent the push was omitted, it must clear this flag!
        if (!need_push)
          _mPushOmitted = true;
        return need_push;
    }

    ScriptAllocator *_mAllocator;
    JSONSymbolDataMap _mSymData {};
    JSONCompilationOptions _mOptions {};
    bool _mPushOmitted = false;
    uint32_t _mJumpNum = 0;

    nlohmann::json::object_t _mFunction;
    nlohmann::json::array_t _mCode;
};

const char * const JSON_TYPE_NAMES[LST_MAX] = {
    "void",
    "integer",
    "float",
    "string",
    "key",
    "vector",
    "rotation",
    "list",
    "ERROR"
};

}
