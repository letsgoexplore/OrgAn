#include <iostream>
#include <pybind11/embed.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>    // for myPyObject.cast<std::vector<T>>()

namespace py = pybind11;

using namespace std;

int main()
{
    std :: cout << "Hello world";
    /*
	PyObject* pInt;

	Py_Initialize();

	PyRun_SimpleString("print('Hello World from Embedded Python!!!')");
	
	Py_Finalize();

	printf("\nPress any key to exit...\n");
	if(!_getch()) _getch();
	return 0;
    */
}
