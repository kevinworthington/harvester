#the following looks through the loaded data extracts the relevant information into a table
from io import StringIO
from html.parser import HTMLParser
import re, json
from datetime import datetime
import csv
from pyproj import Proj, transform

class FileParser:
    def __init__(self,props):
        for p in props:
            setattr(self,p, props[p])

        # create a table to store the processed data
        self.cols = ["Identifier","Title", "Alternative Title", "Description", "Language", "Creator", "Publisher", "Genre",
                     "Subject", "Keyword", "Date", "Issued", "Temporal Coverage", "Date Range", "Solr Year",
                     "Spatial Coverage", "Bounding Box", "Type", "Geometry Type", "Format", "Information", "Download",
                     "MapServer", "FeatureServer", "ImageServer", "TileServer", "Slug", "Provenance", "Code",
                     "Is Part Of", "Status", "Accrual Method", "Date Accessioned", "Rights",
                     "Access Rights","Suppressed", "Child","Is Part Of","Thumbnail"]
        # the basic mapping
        # when black = ignore for now
        self.vals = ["id","title","name", "description", "languages", "owner", "publisher", "",
                     "categories", "tags", "created", "", "", "", "year",
                     "places", "bounding_box", "type", "Geometry Type", "type", "info_page", "download",
                     "ms_url", "fs_url", "is_url","ts_url", "Slug", "publisher", "",# Code used in 'workflow' repo for assigning institution
                     "", "", "Accrual Method", "Date Accessioned", "licenseInfo",
                     "access", "", "","is_part_of","thumbnail"]

        # create an array for all the records - these will be exported as the report
        self.rows=[]

        arc_domain="https://www.arcgis.com"
        self.arc_item_prefix = arc_domain+"/sharing/rest/content/items/"

        # self.arc_journal_prefix = arc_domain+"/apps/MapJournal/index.html?appid="
        # self.arc_webapp_prefix = arc_domain + "/apps/webappviewer/index.html?id="

        self.open_prefix = "https://opendata.arcgis.com/datasets/"

        # define some grouped variable for handeling the data
        self.html_fields=["description","licenseInfo"]

        self.list_fields=["tags","categories","places"]
        self.unix_date_fields = ["created", "modified"]


        # make sure the year is reasonable - get the current for comparison
        self.curr_year = datetime.today().year

        # get the categories to be used in case there are none
        with open(self.categories_file) as outfile:
            self.categories=json.load(outfile)

        csvfile = open(self.places_file, newline='')
        reader = csv.DictReader(csvfile, delimiter='|', quoting=csv.QUOTE_NONE)
        self.places = [row for row in reader]
        outfile.close()

    def create_record(self,r,child_obj=False):
        '''
        look though the metadata and create a record for each item
        Be sure to distinguish between a parent record vs a child record
        child records have
            a parent id

        :param r:
        :return: the modified result for use in assigment to the child record
        '''
        # Because each record could have many layers association with it we need to check for this

        # create new dict for each and assign the remapped values
        _r=dict(r)

        # result doc: https://developers.arcgis.com/rest/users-groups-and-items/search.htm

        _r["bounding_box"]=None
        # reformat extent
        if child_obj is False:
            _r["bounding_box"] = self.get_extent(_r['extent'])
            print( _r["bounding_box"])

        # # todo all parent extent
        # _r["bounding_box"] = []



        ###
        # # note: we're also accounting for child records
        # if child_obj is not False:
        #     _r["is_part_of"] = parent_obj['id']
        #     # change the id to be parent+_+child
        #     _r["id"]= parent_obj['id']+"_"+str(_r["id"])
        #     # adjust the child editingInfo>lastEditDate to be just modified
        #     if "editingInfo" in _r:
        #         _r["modified"] = _r['editingInfo']['lastEditDate']
        #     else:
        #         _r["modified"] = parent_obj["modified"]
        #
        #     # use the parent thumbnail
        #     _r["thumbnail"] = parent_obj['thumbnail']
        #
        #     # use parent bounding box if available - parent should always have this no need to check 'and "bounding_box" in parent_obj'
        #     if _r["bounding_box"] is None :
        #
        #         _r["bounding_box"] = parent_obj["bounding_box"]
        #
        #
        #     # we'll likely have to map some of the parent attributes onto the child since they are a bit different
        #
        #     #
        #     for v in self.vals:
        #         # make sure the variable name is not empty
        #
        #         if v != "":
        #             if not v in _r:
        #                 # lets first check if the variable exists
        #                 # add variable if not exists
        #                 _r[v] =""
        #             if _r[v] is not None and len(_r[v])==0: # comparing on  _r[v] =='' does not work
        #                 # if the variable set is empty and in the parent - use the parent value
        #                 if v in parent_obj:
        #                     _r[v] = parent_obj[v]
            # take the field>name and use as tags
            tags=[]

            if 'fields' in _r and _r['fields'] is not None:
                for f in _r['fields']:
                    tags.append(f['name'])


            _r["tags"]=tags

        # strip the html and none character text - required for csv
        # todo - turn this off when using a database
        for h in self.html_fields:
            print(h in _r, h)
            if h in _r:
                _r[h] = strip_tags(_r[h])
            else:
                print("set to nothing!!!")
                _r[h]=""

        # add some modified values

        # todo keep track of whether we added new pieces of information
        # this will be captured in the database
        _r["categories"] = self.get_categories(_r)

        _r["places"] = self.get_places(_r)

        # try to get the year
        _r["year"] = self.get_year(_r)

        # generate a link to the landing page
        _r["info_page"] = self.open_prefix + _r['id']

        _r["thumb"] =  self.arc_item_prefix + _r['id'] + "/info/" + _r["thumbnail"]

        # not all layers will have the following - need a way to check these
        _r["metadata"] =  self.arc_item_prefix + _r['id'] + "/info/metadata/metadata.xml?format=default"

        # this one is particularly tricky to pin down
        print(_r["type"], _r["type"] not in ["Raster Layer"])
        if _r["type"] not in ["Raster Layer","StoryMap","Web Mapping Application"]:
            # it should also be noted that the zip download links return json with a 'serviceUrl' which actually links to the data
            # todo add all the download links associated with each layer
            # start with the first one
            _r["download"] = self.open_prefix + _r['id']+"_0"+ ".zip"
            print(_r["download"])
            _r["csv"] = self.open_prefix + _r['id'] + ".csv"

            print("DOWNLOAD",_r["download"])

        if _r["type"] in ["StoryMap","Web Mapping Application"]:
            _r["info_page"] =  _r["url"]

        # to show the data the url needs to have '/0' appended for the root record
        # note that the children will each have their 'id' number in place of the 0
        if _r["type"] == "Feature Service":
            _r["fs_url"]=_r["url"]+"/0"

        # note that map services seem to actually be tile map services
        # todo make this more robust by seeking more details to assume correctly
        if _r["type"] == "Map Service":
            _r["ts_url"] = _r["url"]

        print(_r["info_page"])
        # convert lists to strings
        for l in self.list_fields:
            _r[l] = '|'.join(_r[l])


        if isinstance(_r['bounding_box'], list):
            _r["bounding_box"] = ','.join([str(x) for x in _r["bounding_box"]])

        # once we have all the data - put the results in a sharable place
        self.rows.append(_r)
        return _r

    def get_extent(self,extent):
        '''
        get the extent and reproject if needed
        It's a bit slow so only start this if you don't mind waiting
        :param extent:
        :return:
        '''
        print(extent, "the latestWkid")

        _extent=  self.get_extent_xyxy(extent)
        if 'spatialReference' in extent:
            try:
                if 'latestWkid' in extent['spatialReference']:
                    projection=str(extent['spatialReference'][ 'latestWkid'])
                    if  projection!='4326':
                        inProj = Proj(init='epsg:'+projection)

                    else:
                        inProj=None
                else:
                    # custom
                    inProj = Proj(extent['spatialReference'])

                if inProj is not None:
                    outProj = Proj(init='epsg:4326')
                    _extent[0], _extent[1] = transform(inProj, outProj, _extent[0], _extent[1])
                    _extent[2], _extent[3] = transform(inProj, outProj, _extent[2], _extent[3])

            except:
                _extent=None


        return _extent



    def get_extent_xyxy(self,extent):
        # convert from "extent": [[minX, minY],[maxX, maxY]],
        # to minX, minY, maxX, maxY
        extent_list = []
        try:
            if len(extent) > 1:
                extent_list.append(extent[0][0])
                extent_list.append(extent[0][1])
                extent_list.append(extent[1][0])
                extent_list.append(extent[1][1])
        except:
            # make exception for the record layers having a different format
            extent_list = [extent['xmin'], extent['ymin'], extent['xmax'], extent['ymax']]

        return extent_list

    def get_year(self, r):
        # -- get the year --
        text = r['description']

        year = ""

        if text is not None:
            # try to get the year from the description
            regex = "\d{4}"
            match = re.findall(regex, text)

            if len(match) > 0:
                for m in match:
                    if int(m) <= self.curr_year and int(m) > 1500:
                        # loop through look for a reasonable year
                        solrYear = m
            # if still not set - take the year from the modified date
        if year == "":
            year = self.get_utc_from_unix(r["modified"])[:4]

        return year

    def get_categories(self, r):

        categories = r["categories"] # most likely an empty list
        text = r['description']
        # append the keywords

        text += ', '.join(r['tags'])

        match={}
        if len(r["categories"])==0 and text is not None:



            # look through the description and pull out and matches
            # we want to know what keywords are selected from each to assist with improving the keywords being used

            for c in self.categories:

                for k in c["keywords"]:
                    if k in text:

                        if c['name'] not in match:
                            match[c['name']]=[]
                        match[c['name']].append(k)

            r['match'] = match
            # choose the category with the highest number
            count=0
            for m in match:
                new_count = len(match[m])
                if new_count>count:
                    categories=[m]
                    count=new_count

        return categories




    def get_utc_from_unix(self,ts):

        return datetime.utcfromtimestamp(ts/1000).strftime('%Y%m%d')

    def get_results(self,report):
        with open(report, 'w', newline='', encoding='utf-8') as outfile:
            csvout = csv.writer(outfile)
            csvout.writerow(self.cols)
            for r in self.rows:
                all_values=[]
                for v in self.vals:
                    if v != "" and v in r:
                        all_values.append(r[v])
                    else:
                        all_values.append("")
                csvout.writerow(all_values)

    def get_places(self,r):
        '''
        Look through the places file and see if there are any matches with the tags lists
        todo - make this more robust
        :param r:
        :return:
        '''
        places=[]
        tags=r['tags']
        for t in tags:
            # look for a match
            for p in self.places:
                if t.lower() == p['NAME'].lower() or t.lower() == p['NAMELSAD'].lower():
                    if t.title() not in places and t.lower() not in ["trail","basin","wells","hydro","Forest"]:
                        places.append(t.title())



        return places


# https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    if html is None:
        return ""
    s = MLStripper()
    s.feed(html)
    d= s.get_data()
    d = re.sub(r'[\n]+|[\r\n]+', ' ', d, flags=re.S)
    d = re.sub(r'\s{2,}', ' ', d)
    d = d.replace(u"\u2019", "'").replace(u"\u201c", "\"").replace(u"\u201d", "\"").replace(
        u"\u00a0", "").replace(u"\u00b7", "").replace(u"\u2022", "").replace(u"\u2013", "-").replace(u"\u200b","")
    return d