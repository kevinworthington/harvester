import FileManager as fm;


import csv
import os.path
import time
import argparse

# use current directory
directory = os.path.dirname(os.path.realpath(__file__))+"/"
end_point_file="arc_end_points.csv"
categories_file="category.json"
places_file = "places.txt"
report_file = "report.csv"

file_manager = None


def main():
    """
    Use the passed object to start harvesting data from the endpoints

    :param name:
    :return:
    """
    with open(directory+end_point_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # load each end_point
            # inject the data
            row["date"]=file_manager.date
            row["path"] = file_manager.path+"/"+file_manager.data_folder+"/"
            row["num"] = file_manager.num
            row["report_file"] = file_manager.report_file
            # create the file collection
            file_manager.load(row)



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="count")
    parser.add_argument("-l", "--local", help="choose if local run",
                        action="store_true")


    parser.add_argument("-d", "--date", help="(Optional) The date of when to run - useful when wanting to overwrite the run date. Format YYYYMMDD")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if (args.date):
        _date = args.date
    else:
        _date = time.strftime('%Y%m%d')

    file_manager = fm.FileManager({
        "data_folder": "data",
        "num": 100,  # the number of records to collect with each iteration (max 100 determined by Esri)
        "date": _date,
        "path": directory + "/",
        "categories_file":categories_file,
        "places_file": places_file,
        "report_file": report_file
    })

    main()



