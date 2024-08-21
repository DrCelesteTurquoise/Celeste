import os
import csv
import inspect
import logging
import struct
from datetime import datetime
from pathlib import Path

from north.n9_server import send_cmd

class NorthData:
    def __init__(self, labels=[], name=None, save_dir=None, silent_overwrite=False):
        """
        :param list labels:
        :param str name:
        """
        assert isinstance(labels, list)
        self._labels = labels
        proj_dir = Path(save_dir) if save_dir is not None else Path(os.getcwd())
        if not isinstance(name, str):
            name = proj_dir.name

        # handle auto-names
        if name.startswith("#"):
            if name == "#date":
                name = datetime.now().strftime("%b-%d-%y")
            elif name == "#time":
                name = datetime.now().strftime("%H-%M")
            elif name == "#datetime":
                name = datetime.now().strftime("%b-%d-%y_%H-%M")
            elif name == "#number":
                top_num = max( # grab only the highest numeric value
                    map(lambda x: int(x[2:-4]), # grab only the numeric component of filename
                        filter( # grab only .csv files with the correct prefix
                            lambda x: x.endswith(".csv") and x.startswith("n_") and x[2:-4].isnumeric(),
                            os.listdir(proj_dir)) # grab all files in dir
                        )
                )
                name = f'n_{top_num+1}'
            else:
                logging.warning(f'NorthData: Unrecognized auto-name {name}; using {proj_dir.name} instead.')
                name = proj_dir.name

        # determine file path and check if it exists, and if so should it be overwritten?
        self._path = proj_dir.joinpath(f"{name}.csv")
        if Path.exists(self._path) and not silent_overwrite:
            response = input(f'{self._path} exists and will be overwritten. Are you sure? (Y/N)')
            if response.upper() != 'Y':
                raise FileExistsError("NorthData creation cancelled by user.")

        # instantiate the csv file associated with this object
        with open(self._path, mode='w', newline='') as file:
            if len(self._labels) > 0:
                csv.writer(file).writerow(self._labels)
            else:
                pass  # simply create the empty file
        assert isinstance(name, str)
        from north.n9_server import launch_north_server
        launch_north_server()  # creates data broker iff it doesn't exist
        send_cmd(b'DOPE', data=bytes(self._path.name, "ascii"))

    ###################
    # Private methods #
    def _write_row(self, data):
        """
        :param list data:
        """
        try:
            with open(self._path, mode='a', newline='') as file:
                csv.writer(file).writerow(data)
        except Exception:
            logging.exception('in NorthData._write_row()')
        send_cmd(b'DREF', data=bytes(self._path.name, "ascii"))  # refresh the open file

    ##################
    # Public methods #
    def record(self, *args, **kwargs):
        row = [None for _ in enumerate(self._labels)]
        # insert labelled data to the row first
        for label in kwargs:
            value = kwargs[label]
            if label in self._labels:
                pos = self._labels.index(label)
                row[pos] = value
            else:
                logging.error(f'Invalid keyword: {label}, not present in data labels.')

        # find empty slots in the row
        empties = []
        for i, v in enumerate(row):
            if v is None:
                empties.append(i)

        # fill out the row with arguments, starting with empty labelled slots, then to unlabelled slots at the end
        for value in args:
            if len(empties) > 0:
                pos = empties[0]
                del empties[0]
                row[pos] = value
            else:
                row.append(value)

        self._write_row(row)
