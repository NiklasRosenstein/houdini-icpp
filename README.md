# houdini-icpp

An additional layer on top of the Houdini `inlinecpp` module that makes writing,
debugging and distributing Inline-C++ modules easier.

```python
from houdini_icpp import library
_mylib = library('_mylib.icpp')
```

Instead of using `inlinecpp.createLibrary()` and specifying everything inline
with your Python code, `houdini_icpp` allows you to split up every function in
a separate file. One especially huge advantage is that it can add a `#line`
preprocessor to the file, effectively giving you accurate line numbers and file
names on error messages.

## Structure

    _mylib.icpp/
      structs.json
      include.hpp
      functiona.cpp
      functionb.cpp
      functionc.cpp

## Installation

I recommend downloading the source code from this repository and placing it
at some convenient location. In your houdini preference directory
(`$HOME/Documents/houdiniX.X` on Windows), create a `scripts/python/pythonrc.py`
file and add the following:

```python
import sys
sys.path.append("C:/Users/niklas/repos/houdini-icpp")  # Path to where you placed the code
sys.path_importer_cache.clear()
```
