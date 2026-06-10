"""Точка входа: python -m src.db"""

from .tui import TUI


def main() -> None:
    TUI().run()


if __name__ == "__main__":
    main()
