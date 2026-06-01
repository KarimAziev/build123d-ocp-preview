import runpy
import sys


def install_typing_compat() -> None:
    if sys.version_info >= (3, 11):
        return

    import typing

    if not hasattr(typing, "NotRequired"):
        from typing_extensions import NotRequired

        setattr(typing, "NotRequired", NotRequired)


def main() -> int:
    install_typing_compat()

    from ocp_vscode import set_port

    set_port(int(sys.argv[1]))
    runpy.run_path(sys.argv[2], run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
