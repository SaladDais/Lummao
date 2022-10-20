#include <tailslide/tailslide.hh>
#include <tailslide/passes/desugaring.hh>

namespace Tailslide {
class PythonVisitor : public ASTVisitor {
  protected:
  void writeChildrenSep(LSLASTNode *parent, const char *separator);
  void writeFloat(float f_val);
  std::string getSymbolName(LSLSymbol *sym);

  virtual bool visit(LSLScript *script);
  virtual bool visit(LSLGlobalVariable *glob_var);
  virtual bool visit(LSLGlobalFunction *glob_func);
  virtual bool visit(LSLEventHandler *event_handler);
  void visitFuncLike(LSLASTNode *func_like, LSLASTNode *body);

  virtual bool visit(LSLIntegerConstant *int_const);
  virtual bool visit(LSLFloatConstant *float_const);
  virtual bool visit(LSLStringConstant *str_const);
  virtual bool visit(LSLKeyConstant *key_const);
  virtual bool visit(LSLVectorConstant *vec_const);
  virtual bool visit(LSLQuaternionConstant *quat_const);
  virtual bool visit(LSLVectorExpression *vec_expr);
  virtual bool visit(LSLQuaternionExpression *quat_expr);
  virtual bool visit(LSLListConstant *list_const);
  virtual bool visit(LSLListExpression *list_expr);
  virtual bool visit(LSLTypecastExpression *cast_expr);
  virtual bool visit(LSLFunctionExpression *func_expr);
  virtual bool visit(LSLLValueExpression *lvalue);
  void constructMutatedMember(LSLSymbol *sym, LSLIdentifier *member, LSLExpression *rhs);
  virtual bool visit(LSLBinaryExpression *bin_expr);
  virtual bool visit(LSLUnaryExpression *unary_expr);
  virtual bool visit(LSLPrintExpression *print_expr);
  virtual bool visit(LSLParenthesisExpression *parens_expr);
  virtual bool visit(LSLBoolConversionExpression *bool_expr);
  virtual bool visit(LSLConstantExpression *const_expr) { return true; }

  virtual bool visit(LSLNopStatement *nop_stmt);
  virtual bool visit(LSLCompoundStatement *compound_stmt);
  virtual bool visit(LSLExpressionStatement *expr_stmt);
  virtual bool visit(LSLDeclaration *decl_stmt);
  virtual bool visit(LSLIfStatement *if_stmt);
  virtual bool visit(LSLForStatement *for_stmt);
  virtual bool visit(LSLWhileStatement *while_stmt);
  virtual bool visit(LSLDoStatement *do_stmt);
  virtual bool visit(LSLJumpStatement *jump_stmt);
  virtual bool visit(LSLLabel *label_stmt);
  virtual bool visit(LSLReturnStatement *return_stmt);
  void writeReturn(LSLExpression *ret_expr);
  virtual bool visit(LSLStateStatement *state_stmt);

  int _mFuncPreludeTabs = 0;
  std::stringstream _mFuncPreludeStr;
  LSLSymbol *_mFuncSym = nullptr;

  public:
  std::stringstream mStr;
  int mTabs = 0;
  bool mSuppressNextTab = false;

  void doTabs() {
    if (mSuppressNextTab) {
        mSuppressNextTab = false;
        return;
    }
    for(int i=0; i<mTabs; ++i) {
      mStr << "    ";
    }
  }
};
}
