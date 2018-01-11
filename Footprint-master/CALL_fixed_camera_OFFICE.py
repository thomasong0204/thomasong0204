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

import urllib2,psycopg2,math
from shapely import wkb
from shapely.geometry import Polygon
from shapely.affinity import rotate


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

## extract the floor plan to compare
cursor = db.cursor()
cursor.execute("""select * from "osi_office" where name = 'floor';""") ## <== get the floor from the floor plan
floorPlan = cursor.fetchall()

## extract the camera detail
cursor = db.cursor()
cursor.execute("""select * from "osi_camera";""") ## <== get the whole content of fixed lens camera
##cursor.execute("""select * from "osi_camera" where type = 'FIXED';""") ## <== get the whole content of fixed lens camera
CameraList = cursor.fetchall()
for camera in CameraList:
    srid ='3857'
    geometry = camera[0]
    cameraType = camera[1]
##    Floor =camera[2]  ## not in used in office
    camera_UID =camera[2]
    bearing = camera[5]
    focusLength = camera[6]
    cam_height = camera[8]
    sensorWidth = camera[10]
    sensorHeight = camera[11]
    view_angle = camera[16]
    cam_geom = wkb.loads(geometry,hex=True)
    ([cameraX],[cameraY]) = cam_geom.xy



##    if cameraType == "Network camera":
    if cameraType == "FIXED":
##        viewingAngle = float(view_angle) * math.pi /180
        ## change the viewing angle to |\ <= viewing angle
        viewingAngle = (90-float(view_angle)) * math.pi /180
        FOVWidthAngle = 2*math.atan (sensorWidth/(2*focusLength))
        FOVHeightAngle = 2*math.atan(sensorHeight/(2*focusLength))
        bearingRad = (360-bearing)*2*math.pi/360

##        if bearing < 180:
##            bearingRad = (bearing)*2*math.pi/360
##        else:
##            bearingRad = (bearing+180)*2*math.pi/360
        print str(camera_UID)+": "+str(bearingRad)


        cameraToBottom = cam_height*math.tan(viewingAngle-0.5*FOVWidthAngle)
        cameraToTop = cam_height*math.tan(viewingAngle+0.5*FOVWidthAngle)

##       calculate the left and right
        hypoLower = cam_height/(math.cos(viewingAngle-(0.5*FOVHeightAngle)));
        trapBottom = math.tan(0.5*FOVHeightAngle)*hypoLower;

        hypoTop = cam_height/(math.cos(viewingAngle+(0.5*FOVHeightAngle)));
        trapTop = math.tan(0.5*FOVHeightAngle)*hypoTop;
        if trapTop < 0:
            trapTop = abs(trapTop)
        if trapBottom < 0:
            trapBottom = abs(trapBottom)

        if cameraToTop < 0:
            cameraToTop = abs(cameraToTop)
        if cameraToBottom < 0:
            cameraToBottom = abs(cameraToBottom)




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

##        print sqlStatement % (camera_UID,polystarement)

        CheckFootprintExist = """Select count(uid) from office_footprint where uid = '%s';"""
        InsertStatement = """insert into office_footprint(uid,geom) values('%s',%s)"""
        UpdateStatement = """update office_footprint
                                set geom = %s
                            where uid = '%s';"""

        cursor.execute(CheckFootprintExist % (camera_UID))
        queryList = cursor.fetchone()
        if queryList[0] <1:
            ## Insert row
            cursor.execute(InsertStatement % (camera_UID,polystarement))
            db.commit()
        else:
            ## Update row
            cursor.execute(UpdateStatement % (polystarement,camera_UID))
            db.commit()
            print "Update row"
            print "*"*50

    elif cameraType == "DOME":
        viewingAngle = float(view_angle) * math.pi /180
        ## change the viewing angle to |\ <= viewing angle
##        viewingAngle = (90-float(view_angle)) * math.pi /180
        FOVWidthAngle = 2*math.atan (sensorWidth/(2*focusLength))
        FOVHeightAngle = 2*math.atan(sensorHeight/(2*focusLength))
        bearingRad = (360-bearing)*2*math.pi/360

        cameraToBottom = cam_height*math.tan(viewingAngle-0.5*FOVWidthAngle)
        cameraToTop = cam_height*math.tan(viewingAngle+0.5*FOVWidthAngle)

##       calculate the left and right
        hypoLower = cam_height/(math.cos(viewingAngle-(0.5*FOVHeightAngle)));
        trapBottom = math.tan(0.5*FOVHeightAngle)*hypoLower;

        hypoTop = cam_height/(math.cos(viewingAngle+(0.5*FOVHeightAngle)));
        trapTop = math.tan(0.5*FOVHeightAngle)*hypoTop;

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



        polyabc = Polygon(((x4,y2),(x3,y2),(x2,y1),(x1,y1)))
        PolyRotate = rotate(polyabc,bearingRad,cam_geom,use_radians=True)

        polyText = PolyRotate.wkt


        polystarement = "ST_GeomFromText('"+polyText+"',3857)"


##        print sqlStatement % (camera_UID,polystarement)

        CheckFootprintExist = """Select count(uid) from office_footprint where uid = '%s';"""
        InsertStatement = """insert into office_footprint(uid,geom) values('%s',%s)"""
        UpdateStatement = """update office_footprint
                                set geom = %s
                            where uid = '%s';"""

        cursor.execute(CheckFootprintExist % (camera_UID))
        queryList = cursor.fetchone()
        if queryList[0] <1:
            ## Insert row
            cursor.execute(InsertStatement % (camera_UID,polystarement))
            db.commit()
        else:
            ## Update row
            print("==> "+UpdateStatement)
            print UpdateStatement % (polystarement,camera_UID)
            cursor.execute(UpdateStatement % (polystarement,camera_UID))
            db.commit()
            print "*** Update dome row"
            print "*"*30
    else:
        pass




