#!/usr/bin/env python
"""
libusdt bindings for Python
"""

from __future__ import print_function
HAVE_USDT = False
FAKE_DTRACE = False

from ctypes import cdll, c_char_p, c_int, c_void_p, cast

try:
    _libusdt = cdll.LoadLibrary("./libusdt.so")
    HAVE_USDT = True
except:
    pass

if HAVE_USDT:
    usdt_create_provider = _libusdt.usdt_create_provider
    usdt_create_provider.argtypes = [c_char_p, c_char_p]

    usdt_create_probe = _libusdt.usdt_create_probe
    usdt_create_probe.argtypes = [c_char_p, c_char_p, c_int, c_void_p]

    usdt_provider_add_probe = _libusdt.usdt_provider_add_probe
    usdt_provider_enable = _libusdt.usdt_provider_enable
    usdt_fire_probedef = _libusdt.usdt_fire_probedef

    class Probe(object):
        """ a USDT probe """
        def __init__(self, func, name, arg_desc):
            self.length = len(arg_desc)
            args = (c_char_p * self.length)()
            for i in range(self.length):
                args[i] = arg_desc[i]
            self.probedef = usdt_create_probe(func, name, self.length, args)

        def fire(self, args):
            """ fire the probe """
            if len(args) == self.length:
                c_args = (c_void_p * self.length)()
                for i in range(self.length):
                    c_args[i] = cast(args[i], c_void_p)
                usdt_fire_probedef(self.probedef, self.length, c_args)

    class Provider(object):
        """ a USDT provider """
        provider = None
        probes = []
        def __init__(self, provider="python-dtrace", module="default_module"):
            self.provider = usdt_create_provider(provider, module)

        def add_probe(self, probe):
            """ add a probe to this provider """
            self.probes.append(probe)
            usdt_provider_add_probe(self.provider, probe.probedef)

        def enable(self):
            """ enable the provider """
            return(usdt_provider_enable(self.provider))

        def __del__(self):
            pass
else:
    from sys import stderr
    class Probe(object):
        """ a fake USDT probe """
        def __init__(self, name, func, arg_desc):
            self.name = name
            self.func = func
            self.provider = None
        def fire(self, args):
            """ send probe info to stderr if requested """
            if FAKE_DTRACE and self.provider and self.provider.enabled:
                print(self.provider.provider, self.provider.module,
                        self.name, self.func, args,
                        file=stderr)

    class Provider(object):
        """ a fake USDT provider """
        probes = []
        def __init__(self, provider="python-dtrace", module="default_module"):
            self.provider = provider
            self.module = module
            self.enabled = False

        def add_probe(self, probe):
            """ add a probe to this provider """
            self.probes.append(probe)
            probe.provider = self

        def enable(self):
            """ enable this (fake) provider """
            self.enabled = True

        def __del__(self):
            pass

FBT_PROVIDER = Provider("python-dtrace", "fbt")

class fbt(object):
    def __init__(self, f):
        """
        simple function boundary tracing decorator
        """
        self.f = f
        probename = f.__name__
        self.entry_probe = Probe(probename, "entry", ["char *"])
        self.return_probe = Probe(probename, "return", ["char *"])
        FBT_PROVIDER.add_probe(self.entry_probe)
        FBT_PROVIDER.add_probe(self.return_probe)

    def __call__(self, *args):
        self.entry_probe.fire([", ".join(map(str,args))])
        ret = self.f(*args)
        self.return_probe.fire([str(ret)])
        return ret

def enable_fbt():
	FBT_PROVIDER.enable()

def main():
    test_prov = Provider("python", "provmod")
    test_probe = Probe("hello", "name", ["char *"])
    test_prov.add_probe(test_probe)
    test_prov.enable()
    test_probe.fire(["Hello World"])
    @fbt
    def hello(arg1, arg2):
        return True
    enable_fbt()
    hello(1, 2)

if __name__ == "__main__":
    if not HAVE_USDT:
        FAKE_DTRACE = True
    main()
