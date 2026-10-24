"""Load triton's native library with RTLD_DEEPBIND.

The pip builds of tensorflow export the symbols of their bundled LLVM. When libtriton.so (which bundles
a different LLVM) is loaded after tensorflow, its LLVM references bind to tensorflow's copies and the
process segfaults, e.g. `import tensorflow; tf.constant(1); import torchvision` or any torch.compile.
DEEPBIND makes libtriton resolve its own symbols first. Installed via triton_deepbind.pth.
"""
import importlib.abc
import importlib.machinery
import os
import sys

_MODULE = "triton._C.libtriton"


class _DeepBindLoader(importlib.machinery.ExtensionFileLoader):
    def create_module(self, spec):
        flags = sys.getdlopenflags()
        sys.setdlopenflags(flags | os.RTLD_DEEPBIND)
        try:
            return super().create_module(spec)
        finally:
            sys.setdlopenflags(flags)


class _DeepBindFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name != _MODULE:
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is not None and isinstance(spec.loader, importlib.machinery.ExtensionFileLoader):
            spec.loader = _DeepBindLoader(spec.name, spec.origin)
        return spec


sys.meta_path.insert(0, _DeepBindFinder())
