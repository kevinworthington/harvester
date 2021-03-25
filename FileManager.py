import urllib.request, json

import os.path
from os import path

import ssl
import FileParser

fileParser=None


class FileManager:
    '''
    Keep track of all the files to be downloaded.
    There are many, since only 100 responses can be downloaded at a time
    '''
    def __init__(self,props):
        global fileParser

        for p in props:
            setattr(self,p, props[p])

        # create a parsing file and load in the categories
        fileParser=FileParser.FileParser({
            "categories_file":self.path+self.categories_file,
            "places_file": self.path + self.places_file,
            "file_manager":self})

        # create the storage folder if it doesn't exists
        if not path.exists(self.path+self.data_folder):
            os.mkdir(self.path+self.data_folder)

    def load(self,props):
        print(props)
        FileCollection(props)

class FileCollection:
    '''
    Control the REST requests and the passed params
    '''
    def __init__(self,props):
        # take the end point and start loading the data
        for p in props:
            setattr(self, p, props[p])

        self.start=1
        self.page = 1
        self.total=None
        self.folder = self.org_name+"_"+self.date

        if not path.exists(self.path+self.folder):
            os.mkdir(self.path+self.folder)

        self.load_results()

    def load_results(self):
        # declare the folder and file names
        folder_path=self.path+self.folder+"/"
        file=self.org_name+"_p"+str(self.page)+".json"
        _file = folder_path + file
        #check if the data exists
        url = self.end_point + "&start=" + str(self.start) + "&num=" + str(self.num)
        self.load_file_call_func( _file, url,'check_loaded')

    def load_file_call_func(self,_file,_url,_func,parent_obj=False):
        if not path.exists(_file):
            # setup the url to load each request
            # print("loading file", _url)
            urllib.request.urlretrieve(_url, _file)
            try:
                context = ssl._create_unverified_context()
                response = urllib.request.urlopen(_url, context=context)

                newdata = json.load(response)

            except ssl.CertificateError as e:
                print("Data portal URL does not exist: " + _url)

            with open(_file, 'w', encoding='utf-8') as outfile:
                json.dump(newdata, outfile)
                getattr(self, _func)(newdata,parent_obj)
            #
        else:
            # load the file and see whether all the files have been loaded
            with open(_file) as outfile:
                getattr(self, _func)(json.load(outfile),parent_obj)


    def check_loaded(self,data,parent_obj=False):
        # scan the json looking for how many records have been downloaded
        # can setup the next request if there are more pages to be downloaded
        print(data["total"])
        # if there's more data to download - increment the page num and start values
        # if (data["nextStart"] !=-1):
        #     self.start=data["nextStart"]
        #     self.page+=1
        #     self.load_results()
        # todo - allow all the files to be downloaded - uncomment above to harvest them all
        self.drill_loaded_data(data)


        # todo add else for when all done and print the results

        # once all the files have been loaded we should check the results
        fileParser.get_results(self.path+self.report_file)

    def drill_loaded_data(self,data):
        '''
        perform a basic drill down operation looking through the results and loading the attributes
        :param data:
        :return:
        '''
        # start by making sure a 'layers' folder exists
        layers_path=self.path+self.folder+"/layers"
        if not path.exists(layers_path):
            os.mkdir(layers_path)

        for r in data['results']:
            # download the file url+'/layers?f=pjson' - create records for each and associate these records with the parent
            print(r['url'])
            type = r['type']
            r["publisher"] = self.publisher

            if r['url'] is not None:
                # download the file and create records
                # todo it would be nice to highlight the excluded. Note: they will need special treatment
                if type not in ["Web Mapping Application","StoryMap"]:
                    _file = layers_path+"/"+r['id']+".json"
                    _url = r['url']+'/layers?f=pjson'
                    # we need to pass a reference to the parent

                    self.load_file_call_func(_file, _url, 'check_sub_loaded', r)
                else:
                    print("type", type, _url)

                    # artificially add an extent for records that don't have one
                    # todo - need to flag this value for manual inspection
                    if len(r["extent"])==0:
                        r["extent"]=[[-125.102,23.9979992],[-66.134,50.1019992]]
                        fileParser.create_record(r)

            else:
                print("no record created for type", type)


    def check_sub_loaded(self,data,parent_obj):
        '''
        We're going a level deeper here and looking at the layers associated with a record
        We'll create only parent records and associate the children beneath.
        :param data: the sub information to be used in creating more informative compound records
        :return:
        '''

        # todo - associate the children - all details exist in the 'data'

        fileParser.create_record(parent_obj)

        # if there is only 1 layer do not create the parent record
        # create the parent record

        # if len(data['layers'])>1:
        #
        #     parent_obj = fileParser.create_record(parent_obj)
        # else:
        #     parent_obj=False
        #
        # print('layers count',len(data['layers']))
        # for d in data['layers']:
        #
        #
        #     fileParser.create_record(d,parent_obj)
        #
        #

