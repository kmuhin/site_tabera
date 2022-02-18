import csv
from contextlib import contextmanager
import string
from datetime import datetime
from pathlib import Path
from shutil import copyfile

# to avoid double newlines should use either
# csv.Writer(f, lineterminator='\n')
# or 
# open(f, newline='')


def_delimiter = ';'
def_encoding = 'utf-8-sig'


def csv_dict(file, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs):
    with open(file, encoding=encoding) as f:
        for row in csv.DictReader(f, delimiter=csv_delimiter, **kwargs):
            yield row


def csv_list(file, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs):
    with open(file, encoding=encoding) as f:
        for line in csv.reader(f, delimiter=csv_delimiter, **kwargs):
            yield line


@contextmanager
def csv_dictreader(file, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs) -> csv.DictReader:
    f = open(file, encoding=encoding)
    try:
        yield csv.DictReader(f, delimiter=csv_delimiter, **kwargs)
    finally:
        f.close()


@contextmanager
def csv_dictwriter(file, fields, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs) -> csv.DictWriter:
    f = open(file, 'w', encoding=encoding)
    dictwriter = csv.DictWriter(f, fieldnames=fields, delimiter=csv_delimiter, lineterminator='\n', **kwargs)
    dictwriter.writeheader()
    try:
        yield dictwriter
    finally:
        f.close()


@contextmanager
def csv_dictappend(file, fields, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs):
    if isinstance(file, str):
        file = Path(file)
    no_file = False
    if not file.exists():
        no_file = True
    f = open(file, 'a', encoding=encoding)
    dictwriter = csv.DictWriter(f, fieldnames=fields, delimiter=csv_delimiter, lineterminator='\n', **kwargs)
    try:
        if no_file:
            dictwriter.writeheader()
        yield dictwriter
    finally:
        f.close()


@contextmanager
def csv_reader(file, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs) -> csv.reader:
    f = open(file, encoding=encoding)
    try:
        yield csv.reader(f, delimiter=csv_delimiter, **kwargs)
    finally:
        f.close()


@contextmanager
def csv_writer(file, csv_delimiter=def_delimiter, encoding=def_encoding, **kwargs) -> csv.writer:
    f = open(file, 'w', encoding=encoding)
    csvwriter = csv.writer(f, delimiter=csv_delimiter, lineterminator='\n', **kwargs)
    try:
        yield csvwriter
    finally:
        f.close()


def str_to_float(text: str):
    return float(text.replace(',', '.'))


def float_to_str(num: float):
    return str(num).replace('.', ',')


def convert_fields_float_to_str(row: dict, fields: list):
    # При сохранении перевожу поля с float числами в строки с разделителем соответствующим моей локали,
    # в моем случае это ",".
    for col in fields:
        row[col] = float_to_str(row[col])


def convert_fields_str_to_float(row: dict, fields: list):
    for col in fields:
        if not row[col]:
            continue
        row[col] = str_to_float(row[col])


def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    return filename if filename.strip('.') else ''


def backup_file_date(file: Path, backup_dir=None):
    if isinstance(file, str):
        file = Path(file)
    if not file.exists():
        raise FileExistsError(file)
    backup_dir = backup_dir if backup_dir else file.parent
    if not backup_dir.exists():
        raise FileExistsError(backup_dir)
    backup_name_suffix = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_name = f'{file.stem}-{backup_name_suffix}{file.suffix}'
    backup_file = backup_dir.joinpath(backup_name)
    copyfile(file, backup_file)
    return backup_file
