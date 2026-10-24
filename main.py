"""Ponto de entrada compatível do aplicativo CurvSat."""

from __future__ import annotations


if __name__ == "__main__":
    import runpy

    runpy.run_module("curvsat.application", run_name="__main__")
else:
    from curvsat.application import *  # noqa: F401,F403
