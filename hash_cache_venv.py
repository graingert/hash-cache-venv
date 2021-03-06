"""
get or a create a cached virtual environment based on requirements

usage: ENV_DIR=$(hash-cache-venv requirements-pypa.txt requirements.txt)
"""
__version__ = "0.0.0.post0"

import errno
import hashlib
import io
import json
import os.path
import subprocess
import sys

import appdirs
import filelock
import packaging.markers
import virtualenv

expected_header = u"""\
#
# This file is autogenerated by pip-compile
"""

APP_NAME = "hash-cache-venv"
APP_AUTHOR = "graingert"

CACHE_INFO = u"""\
This is the cache dir for hash-cache-venv

see https://github.com/graingert/hash-cache-venv for more information!
"""


def _has_venv():
    try:
        __import__("venv")
        return True
    except ImportError:
        return False


def _process_requirements_file(path):
    with io.open(path, "r", encoding="utf8") as f:
        actual_header = f.read(len(expected_header))
        if actual_header != expected_header:
            raise Exception(
                "not a pip-compiled file "
                "{path!r} {actual_header!r} != {expected_header!r}".format(
                    path=path,
                    actual_header=actual_header,
                    expected_header=expected_header,
                )
            )
        return f.read()


def run(requirements_paths):
    cache_dir = os.environ.get("HASH_CACHE_VENV_DIR") or appdirs.user_cache_dir(
        appname=APP_NAME, appauthor=APP_AUTHOR, version=__version__
    )

    key = hashlib.sha256(
        json.dumps(
            {
                "environment": packaging.markers.default_environment(),
                "requirements": [
                    _process_requirements_file(p) for p in requirements_paths
                ],
            },
            sort_keys=True,
            ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()

    workdir = os.path.join(cache_dir, key[0:2], key[2:4], key[4:6], key[6:])

    try:
        os.makedirs(workdir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    donefile = os.path.join(workdir, ".done")
    lock_file = os.path.join(workdir, ".lock")
    venvdir = os.path.join(workdir, "venv")

    creator = "venv" if _has_venv() else "builtin"

    with filelock.FileLock(lock_file):
        with io.open(
            os.path.join(cache_dir, "readme.txt"), "w", encoding="utf8"
        ) as info_file:
            info_file.write(CACHE_INFO)

        if os.path.isfile(donefile):
            return venvdir

        exe = virtualenv.cli_run(
            ["--no-periodic-update", "--creator={}".format(creator), "--", venvdir]
        ).creator.exe

        for requirements in requirements_paths:
            subprocess.check_call(
                [
                    str(exe),
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "--require-hashes",
                    "--requirement",
                    requirements,
                ],
                stdout=sys.stderr.fileno(),
            )
        with io.open(donefile, "w", encoding="utf8") as done:
            done.write(u"DONE!")

    return venvdir


def main(argv=sys.argv):
    print(run(argv[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
