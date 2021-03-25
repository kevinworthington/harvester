import FileManager as fm;


import csv
import os.path
import time
import argparse

import glob


out_file ="places.txt"
in_folder="places"
search_pattern='/*/*INCPLACE.txt'
skip_first=True# skip the first line of subsequent files

directory = os.path.dirname(os.path.realpath(__file__))+"/"

# files from https://www.census.gov/geographies/reference-files/time-series/geo/name-lookup-tables.html

def main():
    """
    open all the files and append them to the places
    :param name:
    :return:
    """
    # start with a fresh file
    open(directory+out_file, 'w').close()

    o_file = open(directory+out_file, 'a+')
    files = glob.glob(directory+in_folder+search_pattern)
    for count, f in enumerate(files):
        f_c = open(f, 'r')
        if skip_first and count!=0:
            lines= f_c.readlines()[1:]
            for l in lines:
                o_file.write(l)
        else:
            o_file.write(f_c.read())
        f_c.close()
    o_file.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="count")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()


    main()



