# Copyright (c) 2017 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
An additional layer on top of the Houdini `inlinecpp` module that makes writing,
debugging and distributing Inline-C++ modules easier.
"""

from __future__ import print_function
from hutil import cppinline
from collections import Sequence

import contextlib
import hou
import inlinecpp
import json
import os


path = [os.path.dirname(__file__)]


@contextlib.contextmanager
def swapmember(obj, member, new_value):
  old_value = getattr(obj, member)
  setattr(obj, member, new_value)
  try:
    yield
  finally:
    setattr(obj, member, old_value)


def load_json(fp):
  """
  Uses #json.load(), but parses objects into ordered tuples and converts
  unicode strings to (byte) strings.
  """

  result = json.load(fp, object_pairs_hook=tuple)

  # Convert unicode to strings.
  def convert(obj):
    if isinstance(obj, unicode):
      return obj.encode('utf8')
    elif isinstance(obj, Sequence):
      return tuple(convert(x) for x in obj)
    return obj

  return convert(result)


def library(directory, name=None):
  """
  Loads from *directory* the code to pass into #inlinecpp.createLibrary(). A
  `structs.json` and `includes.hpp` file and all files ending with `.cpp` will
  be taken into account.

  A relative *directory* path will be considered relative to #hou.hipFile.path().
  """

  if not os.path.isabs(directory):
    search_path = [os.path.dirname(hou.hipFile.path())] + path
    for search_dir in search_path:
      new_dir = os.path.join(search_dir, directory)
      if os.path.isdir(new_dir):
        directory = new_dir
        break
    else:
      raise ValueError('Could not find {!r}'.format(directory))

  if not name:
    name = os.path.splitext(os.path.basename(directory))[0]

  structs = []
  structs_fn = os.path.join(directory, 'structs.json')
  if os.path.isfile(structs_fn):
    with open(structs_fn) as fp:
      structs = load_json(fp)

  includes = ""
  includes_fn = os.path.join(directory, 'include.hpp')
  if os.path.isfile(includes_fn):
    with open(includes_fn) as fp:
      includes_fn = includes_fn.replace('\\', '/')
      includes = fp.read()
      includes = '\n#line 1 "{}"\n'.format(includes_fn) + includes

  functions = []
  for fname in os.listdir(directory):
    fname = os.path.join(directory, fname)
    if fname.endswith('.cpp'):
      with open(fname) as fp:
        fname = fname.replace('\\', '/')
        content = fp.read()
        content = '\n#line 1 "{}"\n'.format(fname) + content
        functions.append(content)

  if not functions:
    raise ValueError('no .cpp files in {!r}'.format(directory))

  with swapmember(cppinline, '_CPPFunction', iCPPFunction):
    return inlinecpp.createLibrary(
        name = name, structs = structs, includes = includes,
        function_sources = functions)


class iCPPFunction(cppinline._CPPFunction):
  """
  Overwrites #cppinline._CPPFunction._parse_signature_from_source() as its
  original implementation does not allow any content before the actual function
  source code, and #library() adds a `#line` directive.
  """

  def _parse_signature_from_source(self, source, cpp_type_structs_dict):
    if source.startswith('\n#line'):
      source = source.split('\n', 2)[2]
    return super(iCPPFunction, self)._parse_signature_from_source(source, cpp_type_structs_dict)
