import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (
    BASE_DIR, DATETIME_FORMAT, FILE_OUTPUT_ARG,
    PRETTY_OUTPUT_ARG, RESULTS_DIR_NAME
)

from utils import build_dir


WHERE_IS_FILE_MESSAGE = 'Файл сохранён. Путь: {path}'


def control_output(results, cli_args):
    FUNCTION_TO_OUTPUT[cli_args.output](results, cli_args)


def default_output(results, *args):
    for row in results:
        print(*row)


def pretty_output(results, *args):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    dir = build_dir(BASE_DIR, RESULTS_DIR_NAME)
    parser_mode = cli_args.mode
    now = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now}.csv'
    file_path = dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect=csv.unix_dialect)
        writer.writerows(results)
    logging.info(WHERE_IS_FILE_MESSAGE.format(path=file_path))


FUNCTION_TO_OUTPUT = {
    FILE_OUTPUT_ARG: file_output,
    PRETTY_OUTPUT_ARG: pretty_output,
    None: default_output
}
