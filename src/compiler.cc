#include "python_pass.hh"
#include <string>

#define PY_SSIZE_T_CLEAN 1
#include <Python.h>

using namespace Tailslide;

static PyObject* set_error(const char* message)
{
  PyObject *mod_lummao = PyImport_ImportModule("lummao.exceptions");
  assert (mod_lummao != NULL);
  PyObject* type_compile_error = PyObject_GetAttrString(mod_lummao, "CompileError");
  assert (type_compile_error != NULL);

  PyErr_SetString(type_compile_error, message);
  return nullptr;
}

PyObject* lsl_to_python_src(PyObject* self, PyObject *args, PyObject *kwargs) {
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
    // TODO: output the actual errors
    return set_error("Error occurred during compilation");
  }

  PythonVisitor py_visitor;
  script->visit(&py_visitor);
  std::string py_code {py_visitor.mStr.str()};
  return PyBytes_FromStringAndSize(py_code.c_str(), py_code.size());
}


static PyMethodDef compilerMethods[] = {
  {"lsl_to_python_src", (PyCFunction) lsl_to_python_src, METH_VARARGS, NULL},
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
