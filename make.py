import re
from Cython.Build import cythonize
from sysconfig import get_paths
from subprocess import check_call
from pathlib import Path

from llvmlite import binding as llvm

PYTHON_INCLUDE = get_paths()["include"]
INCLUDE = [PYTHON_INCLUDE]


def main():

    ll_path = compile_cython_to_llvmir("objective_function.pyx")
    api = extract_public_api_from_pxd(ll_path.with_suffix(".pxd"))

    process_llvm(ll_path, api)


def compile_cython_to_llvmir(src) -> Path:
    """
    Compiles a Cython source file to LLVM IR.

    Args:
        src (Path): The path to the Cython source file to compile.

    Returns:
        Path: The path to the generated LLVM IR file.
    """
    [ext] = cythonize(src)
    [csrc] = ext.sources

    cmd_inc = " ".join(map(lambda x: f"-I{x}", INCLUDE))
    cmd_src = str(csrc)
    cmd_out = Path(csrc).with_suffix(".ll")
    check_call(["clang", cmd_inc, "-S", "-emit-llvm", cmd_src, "-o", cmd_out])
    assert cmd_out.exists()
    return cmd_out


def extract_public_api_from_pxd(file_path):
    """
    Extracts the public API from a .pxd file.

    Parameters:
    - file_path: The path to the .pxd file.

    Returns:
    - A list of tuples, where each tuple contains the
        (function name, parameters, return_type, keywords, attrs)
    """
    public_api = []

    with open(file_path, "r") as file:
        content = file.read()

        # Regular expression to match function declarations
        # This pattern assumes functions are declared with 'cpdef' or 'def'
        # and captures the function name and parameters.
        pattern = re.compile(r"cdef\s+((?:\w+\s*)+)\((.*)\)(.*)")

        for match in pattern.finditer(content):
            leadings, params, attrs = match.groups()
            leadings = leadings.split()
            function_name = leadings[-1].strip()
            return_type = leadings[-2].strip()
            keywords = leadings[:-2]
            parameters = tuple(map(lambda x: x.strip(), params.split(",")))
            public_api.append(
                (function_name, parameters, return_type, keywords, attrs)
            )

    return public_api


def process_llvm(ll_path, api):
    """
    Processes an LLVM IR file and prints information about the functions defined
    in the file.

    Args:
        ll_path (str): The path to the LLVM IR file to process.
        api (list): See return type of `extract_public_api_from_pxd()`

    Returns:
        None
    """

    with open(ll_path, "r") as fin:
        body = fin.read()
        llmod = llvm.parse_assembly(body)

    for fname, params, retty, *_ in api:
        fn = llmod.get_function(fname)
        print("#", params, "->", retty)
        print(fn)


if __name__ == "__main__":
    main()
