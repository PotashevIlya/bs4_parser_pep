from pathlib import Path

BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR_NAME = 'downloads'
RESULTS_DIR_NAME = 'results'
LOG_DIR_NAME = 'logs'
LOG_FILE_NAME = 'parser.log'


PRETTY_OUTPUT_ARG = 'pretty'
FILE_OUTPUT_ARG = 'file'

DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_PEPS_URL = 'https://peps.python.org/'

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
