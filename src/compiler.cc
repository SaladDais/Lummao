#include "python_pass.hh"
#include "json_ir_pass.hh"
#include <string>

#define PY_SSIZE_T_CLEAN 1
#include <Python.h>

using namespace Tailslide;

static PyObject* set_error(Logger *logger)
{
  PyObject *mod_lummao = PyImport_ImportModule("lummao.exceptions");
  assert (mod_lummao != NULL);
  PyObject* type_compile_error = PyObject_GetAttrString(mod_lummao, "CompileError");
  assert (type_compile_error != NULL);

  auto &messages = logger->getMessages();
  PyObject *message_tup = PyTuple_New(messages.size());
  int idx = 0;
  for (const auto &message : messages) {
    PyObject *err_str = PyUnicode_FromString(message->getMessage().c_str());
    PyTuple_SetItem(message_tup, idx, err_str);
    ++idx;
  }

  // Need to do this or exceptions with only one error will
  // be treated differently.
  PyObject *err_args = PyTuple_New(1);
  PyTuple_SetItem(err_args, 0, message_tup);
  PyErr_SetObject(type_compile_error, err_args);
  return nullptr;
}


enum LSLHandleMode {
    LSL_TO_PYTHON,
    LSL_TO_IR,
} eLSLHandleMode;


PyObject* parse_and_handle_lsl(LSLHandleMode mode, PyObject* self, PyObject *args, PyObject *kwargs) {
  PyObject *buffer;
  if (!PyArg_ParseTuple(args, "O", &buffer))
  {
    // exception is already set
    return NULL;
  }

  char *buffer_data;
  Py_ssize_t buffer_len;
  if (PyBytes_AsStringAndSize(buffer, &buffer_data, &buffer_len) < 0)
  {
    // exception is already set
    return NULL;
  }

  // set up the allocator and logger
  ScopedScriptParser parser(nullptr);
  Logger *logger = &parser.logger;

  auto script = parser.parseLSLBytes(buffer_data, buffer_len);

  if (script) {
    script->collectSymbols();
    script->determineTypes();
    script->recalculateReferenceData();
    script->propagateValues();
    script->finalPass();

    if (!logger->getErrors()) {
      script->validateGlobals(true);
      script->checkSymbols();
    }
  }
  if (logger->getErrors()) {
    return set_error(logger);
  }

  switch (mode) {
    case LSL_TO_PYTHON: {
      PythonVisitor py_visitor;
      script->visit(&py_visitor);
      std::string py_code {py_visitor.mStr.str()};
      return PyBytes_FromStringAndSize(py_code.c_str(), py_code.size());
    }
    case LSL_TO_IR: {
      JSONScriptCompiler json_visitor(&parser.allocator, {true});
      script->visit(&json_visitor);
      std::stringstream sstr;
      sstr << std::setw(2) << json_visitor.mIR << "\n";
      std::string json_str {sstr.str()};
      return PyBytes_FromStringAndSize(json_str.c_str(), json_str.size());
    }
  }
  return nullptr;
}

PyObject* lsl_to_python_src(PyObject* self, PyObject *args, PyObject *kwargs) {
  return parse_and_handle_lsl(LSL_TO_PYTHON, self, args, kwargs);
}

PyObject* lsl_to_ir(PyObject* self, PyObject *args, PyObject *kwargs) {
  return parse_and_handle_lsl(LSL_TO_IR, self, args, kwargs);
}


static PyMethodDef compilerMethods[] = {
  {"lsl_to_python_src", (PyCFunction) lsl_to_python_src, METH_VARARGS, NULL},
  {"lsl_to_ir", (PyCFunction) lsl_to_ir, METH_VARARGS, NULL},
  {NULL, NULL, 0, NULL}       /* Sentinel */
};

static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "lummao._compiler",
  0,                    /* m_doc */
  0,                    /* m_size */
  compilerMethods,      /* m_methods */
};

PyMODINIT_FUNC PyInit__compiler(void)
{
  PyObject* module;

  // This function is not supported in PyPy.
  if ((module = PyState_FindModule(&moduledef)) != NULL)
  {
    Py_INCREF(module);
    return module;
  }

  module = PyModule_Create(&moduledef);
  if (module == NULL)
  {
    return NULL;
  }

  tailslide_init_builtins(nullptr);

  return module;
}
