import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from constants import (
    BASE_DIR, LOG_DIR_NAME, LOG_FILE_NAME, FILE_OUTPUT_ARG, PRETTY_OUTPUT_ARG
)
from utils import build_dir

LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=(PRETTY_OUTPUT_ARG, FILE_OUTPUT_ARG),
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    dir = build_dir(BASE_DIR, LOG_DIR_NAME)
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(
            RotatingFileHandler(
                dir / LOG_FILE_NAME,
                maxBytes=10 ** 6,
                backupCount=5,
                encoding='utf-8'
            ),
            logging.StreamHandler(stream=sys.stdout)
        )
    )
