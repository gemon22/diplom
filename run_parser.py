"""Запуск парсера из корня проекта: python run_parser.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from parser import Parser

if __name__ == "__main__":
    Parser().run()
