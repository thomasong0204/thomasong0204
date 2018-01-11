#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      thomas
#
# Created:     20/12/2017
# Copyright:   (c) thomas 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import urllib2,psycopg2,math,httplib,urllib,re
from shapely import wkb
from shapely.geometry import Polygon
from shapely.affinity import rotate
from bs4 import BeautifulSoup



def ConvertHextoDegree(HexIn):
    RCon = int(HexIn,16)/10000
    DegreeOut = (RCon/ (2 * math.pi)) *360
    return DegreeOut

def ConvertHextoZoom(HexIn):
    ZoomCon = int(HexIn,16)/10
    return ZoomCon


def DecodeRotation(camURL):
    CamResult = urllib2.urlopen(camURL)
    BSResult = BeautifulSoup(CamResult, "lxml")
    result =  str(BSResult.result.str.get_text())
    cleanstr = result.replace(" ","")[-4:]
    resultDegree =ConvertHextoDegree(cleanstr)
    return resultDegree

def DecodeZoom(camURL):
    CamResult = urllib2.urlopen(camURL)
    BSResult = BeautifulSoup(CamResult, "lxml")
    result =  str(BSResult.result.str.get_text())
    cleanstr = result.replace(" ","")[-3:]
    Zoom =ConvertHextoZoom(cleanstr)
    return Zoom



db="osi_social_db"
dbuser="postgres"
dbpassword=""
dbhost="192.168.8.12"
dbport="5432"

## load data
splitwords =[]
Filter_Stop = []

## Load data from postgres
db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

cursor = db.cursor()
##cursor.execute('delete from "cam_footprint";') ## <== delete the older data.
cursor.execute("""select * from "camera" where type = 'Fixed dome';""") ## <== Query to get the list of rotatable camera

CameraList = cursor.fetchall()

for camera in CameraList:
    srid ='3857'
    geometry = camera[0]
    cameraType = camera[1]
    Floor =camera[2]
    camera_UID =camera[3]
    bearing = camera[6]
    focusLength = camera[7]
    cam_height = camera[9]
    sensorWidth = camera[11]
    sensorHeight = camera[12]
    rotateXY = camera[13]
    rotateZ = camera[14]
    OZoom = camera[15]
    DZoom = camera[16]
    view_angle = camera[17]
    cam_geom = wkb.loads(geometry,hex=True)[0]
    ([cameraX],[cameraY]) = cam_geom.xy


    if cameraType == "Fixed dome":
##        viewingAngle = float(view_angle) * math.pi /180
        ## change the viewing angle to |\ <= viewing angle
        cameraXYResult = DecodeRotation(rotateXY)
        cameraZResult = DecodeRotation(rotateZ)
        viewingAngle = float(cameraZResult) * math.pi /180

        OptZoom = DecodeZoom(OZoom)
        FOVWidthAngle = 2*math.atan (sensorWidth/(2*focusLength*OptZoom))
        FOVHeightAngle = 2*math.atan(sensorHeight/(2*focusLength*OptZoom))

        bearingRad = round(cameraXYResult,5)*math.pi/360

        cameraToBottom = cam_height*math.tan(viewingAngle-0.5*FOVWidthAngle)
        cameraToTop = cam_height*math.tan(viewingAngle+0.5*FOVWidthAngle)

##       calculate the left and right
        hypoLower = cam_height/(math.cos(viewingAngle-(0.5*FOVHeightAngle)));
        trapBottom = math.tan(0.5*FOVHeightAngle)*hypoLower;

        hypoTop = cam_height/(math.cos(viewingAngle+(0.5*FOVHeightAngle)));
        trapTop = math.tan(0.5*FOVHeightAngle)*hypoTop;

        print trapTop
        print trapBottom
        ## Coordinate in this order.
        ## x4,y2 ------------ x3,y2
        ##   |    (x4+x3)/2    |
        ##    |              |
        ## x2,y1 ---------- x1,y1
        x1 = float(cameraX + trapBottom);
        x2 = float(cameraX - trapBottom);
        x3 = float(cameraX + trapTop);
        x4 = float(cameraX - trapTop);

        y1 = float(cameraY + cameraToBottom);
        y2 = float(cameraY + cameraToTop);

        polyabc = Polygon(((x4,y2),(x3,y2),(x1,y1),(x2,y1)))
        PolyRotate = rotate(polyabc,bearingRad,cam_geom,use_radians=True)

        polyText = PolyRotate.wkt

        polystarement = "ST_GeomFromText('"+polyText+"',3857)"
        print ("polystarement: "+polystarement)
        print ("camera_UID: "+camera_UID)

        ## Check if the camera id exist in the footprint.
        ## Update footprint if exist.
        ## insert if not
        CheckFootprintExist = """Select count(uid) from cam_footprint where uid = '%s';"""
        InsertStatement = """insert into cam_footprint(uid,geom,floor) values('%s',%s,%s)"""
        UpdateStatement = """update cam_footprint
                                set geom = %s,
                                floor = %s
                            where uid = '%s';"""

        cursor.execute(CheckFootprintExist % (camera_UID))
        queryList = cursor.fetchone()
        if queryList[0] <1:
            ## Insert row
            cursor.execute(InsertStatement % (camera_UID,polystarement,Floor))
            db.commit()
            print "Insert row"
            print "*"*50

        else:
            ## Update row
            cursor.execute(UpdateStatement % (polystarement,Floor,camera_UID))
            db.commit()
            print "Update row"
            print "*"*50



##      //Flip the number if it's negative.
##      if(cameraToTop<0){
##        cameraToTop = math.abs(cameraToTop)
##      }
##
##      if(cameraToBottom<0){
##        cameraToBottom = math.abs(cameraToBottom)
##      }
##

##
##      /// calculate the left and right
## hypoLower = cam_height/(math.cos(viewingAngle-(0.5*FOVHeightAngle)));
## trapBottom = math.tan(0.5*FOVHeightAngle)*hypoLower;
##
## hypoTop = cam_height/(math.cos(viewingAngle+(0.5*FOVHeightAngle)));
## trapTop = math.tan(0.5*FOVHeightAngle)*hypoTop;
##
##      //Flip the number if it's negative.
##      if(trapTop<0){
##        trapTop = math.abs(trapTop);
##      }
##      if(trapBottom<0){
##        trapBottom = math.abs(trapBottom);
##      }
##
##

##
## x1 = parseFloat(cameraX + trapBottom);
## x2 = parseFloat(cameraX - trapBottom);
## x3 = parseFloat(cameraX + trapTop);
## x4 = parseFloat(cameraX - trapTop);
####
## y1 = parseFloat(cameraY + cameraToBottom);
## y2 = parseFloat(cameraY + cameraToTop);
##
##
##      var Footprint = [[x3, ((x4+x3)/2), x4, ((x3+x2)/2), ((x4+x3)/2),((x4+x1)/2),  x2,((x2+x1)/2),x1],
##      [y2,y2,y2, ((y1+y2)/2), ((y1+y2)/2), ((y1+y2)/2), y1,y1,y1],[1,1,1,1,1,1,1,1,1]];
##
##

