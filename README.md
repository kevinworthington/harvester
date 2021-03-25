The following project allow the havesting from multiple organizational ArcGIS collections
These data are exported to allow discovery from alternative platforms (i.e GeoBlacklight)

Start by declaring the arc_end_points in the csv.

| org_name | end_point | publisher |
| --- | ----------- | ----|
| organization name | URL to harvest | name of publisher|

Note the end_point URL doesn't need to return all the data as this program
will iterate over the returned results


Run the program by calling from the command line
```
python ./harvester
```

Or while testing data from a previous harvest use the -d YYYMMDD arg
```
python ./harvester -d 20210312
```

*Note: this program is intended to only be run once a day.
To run this program at a higher frequency, the last harvested data must first be removed*


If it doesn't exist, the 'data' folder will be created, 
and within it, a folder titled with the org_name followed by the date of harvest

Each endpoint will be iterated over, storing a copy of the raw harvested result
within the associated folder. If a file already exists with same name it will not be downloaded.

For clarity, downloaded files are titled using the *org_name* and *page number* of the download file.
Requested end_points will append with '&num=100' followed by '&start=1' to start, and 
repeated until the total number of records has been exhausted.

Once the data is downloaded it's time to parse through each of the results
- to get the layers available: go to the url of each layer - add '?f=pjson' and strip the 'layers' list
- get the layer attributes by going to each of the layers - add /{layer_id}?f=pjson  and strip the 'fields'
to get the metadata - https://www.arcgis.com/sharing/rest/content/items/{result_id}/info/metadata/metadata.xml 
Establishing links to: 
    A thumbnail ...

The resulting table (data/report.csv) can then be passed to [https://github.com/BTAA-Geospatial-Data-Project/workflow](https://github.com/BTAA-Geospatial-Data-Project/workflow)
for GeoBlacklight json generation and Solr ingestion.