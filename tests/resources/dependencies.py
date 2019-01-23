from contextlib import contextmanager
from inspect import signature

from squid_py.keeper.web3_provider import Web3Provider


@contextmanager
def inject_dependencies(klass, *args, **kwargs):
    dependencies = kwargs.pop('dependencies', {})
    klass_parameters = signature(klass).parameters

    to_restore = []

    def patch_provider(object, property, mock):
        to_restore.append((object, property, getattr(object, property)))
        setattr(object, property, mock)

    def patch_dependency(object, property, name):
        if name not in dependencies:
            return

        mock = dependencies[name]
        patch_provider(object, property, mock)

    for name, mock in dependencies.items():
        if name in klass_parameters:
            kwargs[name] = mock
    patch_dependency(Web3Provider, '_web3', 'web3')
    try:
        yield klass(*args, **kwargs)
    finally:
        for (object, property, value) in to_restore:
            setattr(object, property, value)
