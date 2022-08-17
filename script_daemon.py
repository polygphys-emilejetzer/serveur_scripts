# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 13:27:07 2022 par emilejetzer."""

from typing import Callable
from functools import wraps
from threading import Thread
from importlib import import_module
from pathlib import Path

import os

import daemon


def daemonize(f: Callable):
    @wraps(f)
    def F(*args, **kargs):
        with daemon.DaemonContext():
            f(*args, **kargs)

    return F


def run_in_dir(f: Callable, wdir: str):
    @wraps(f)
    def F(*args, **kargs):
        vieux_wdir = os.getcwd()

        try:
            os.chdir(wdir)
            f(*args, **kargs)
        finally:
            os.chdir(vieux_wdir)

    return F


def serial_daemonizer(fs: tuple[Callable]):
    for f in fs:
        yield daemonize(f)


def threader(fs: tuple[Callable], wdir: str = '.') -> tuple[Thread]:
    return tuple(Thread(target=run_in_dir(f, wdir)) for f in fs)


def thread(fs: tuple[Callable], timeout: float = None):
    threads = threader(fs)

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout)


@daemonize
def thread_scripts(répertoire: Path):
    threads = (import_module(x.stem).main for x in répertoire.glob('*.py'))
    thread(threads)


if __name__ == '__main__':
    thread_scripts(Path('./racine/').resolve())
