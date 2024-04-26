from libc.math cimport sin, cos



cdef public api void dfdx(double* x, double* result) noexcept nogil:
    result[0] = -sin(x[0])

cdef public api void f(double* x, double* result) noexcept nogil:
    result[0] = cos(x[0]) + 1
