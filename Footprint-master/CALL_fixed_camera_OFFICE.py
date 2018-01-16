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



import math
import psycopg2
from shapely import wkb
from shapely.geometry import Polygon
from shapely.affinity import rotate
from shapely.wkt import dump
import re

def breakMultiPoly():
	## this module is created a some polgon creates multipolygon after the clipping
    ## not beiong actived at this moment as we don't encounter this issue.

   pass


def ReformBackShape(bearingRad,PolyRotate,x2,x1,y1):
## this is needed to repair the geometry. After clipping, the outline of the feature are changed to more than 4 points
## thus, a need to repair to ensure the geometry are back to 4 points.
	rotateback = 2*math.pi-bearingRad
	PolyRotate = rotate(PolyRotate,rotateback,cam_geom,use_radians=True)
	OldPolyBB = PolyRotate.bounds
	Minx = OldPolyBB[0]
	Maxx = OldPolyBB[2]
	Maxy = OldPolyBB[3]
   ## Coordinate in this order.
   ## x4,y2 ------------ x3,y2
   ##   |    (x4+x3)/2    |
   ##    |              |
   ## x2,y1 ---------- x1,y1
	## compare to check if there's any clipping in the x1 positon.
	## update if there is.
	if Minx > x2:
		newx2 = Minx
	else:
		newx2 = x2

	if Maxx < x1:
		newx1 = Maxx
	else:
		newx1 = x1
	## recreate the polygon
	ReformPoly = Polygon(((Minx,Maxy),(Maxx,Maxy),(newx1,y1),(newx2,y1)))

    ## rotation to be done in javascript

	return ReformPoly


def CreateFixedFootprint(view_angle, sensorWidth, sensorHeight, focusLength, bearing, cameraX, cameraY):
	viewingAngle = (90-float(view_angle)) * math.pi /180
	FOVWidthAngle = 2*math.atan(sensorWidth/(2*focusLength))
	FOVHeightAngle = 2*math.atan(sensorHeight/(2*focusLength))
	bearingRad = (360-bearing)*2*math.pi/360
	cameraToBottom = cam_height*math.tan(viewingAngle-0.5*FOVWidthAngle)
	cameraToTop = cam_height*math.tan(viewingAngle+0.5*FOVWidthAngle)
	##  calculate the left and right
	hypoLower = cam_height/(math.cos(viewingAngle-(0.5*FOVHeightAngle)))
	trapBottom = math.tan(0.5*FOVHeightAngle)*hypoLower
	hypoTop = cam_height/(math.cos(viewingAngle+(0.5*FOVHeightAngle)))
	trapTop = math.tan(0.5*FOVHeightAngle)*hypoTop
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
	x1 = float(cameraX + trapBottom)
	x2 = float(cameraX - trapBottom)
	x3 = float(cameraX + trapTop)
	x4 = float(cameraX - trapTop)
	y1 = float(cameraY + cameraToBottom)
	y2 = float(cameraY + cameraToTop)
	polyabc = Polygon(((x4,y2),(x3,y2),(x1,y1),(x2,y1)))
	PolyRotate = rotate(polyabc,bearingRad,cam_geom,use_radians=True)

	## operation to join floorplan with the floor print
	PolyRotate = floorplanPoly.intersection(PolyRotate).convex_hull
	PolyRotateB = ReformBackShape(bearingRad,PolyRotate,x2,x1,y1) ## Rotate and adjust the polygon back to 4 corner

	polyText = PolyRotateB.wkt
	return polyText



def CreateDOMEFootprint(view_angle,sensorWidth,sensorHeight,focusLength,bearing,cameraX,cameraY):
    viewingAngle = (90-float(view_angle)) * math.pi /180
    FOVWidthAngle = 2*math.atan (sensorWidth/(2*focusLength))
    FOVHeightAngle = 2*math.atan(sensorHeight/(2*focusLength))
    bearingRad = (360-bearing)*2*math.pi/360
    cameraToBottom = cam_height*math.tan(viewingAngle-0.5*FOVWidthAngle)
    cameraToTop = cam_height*math.tan(viewingAngle+0.5*FOVWidthAngle)
    ##  calculate the left and right
    hypoLower = cam_height/(math.cos(viewingAngle-(0.5*FOVHeightAngle)))
    trapBottom = math.tan(0.5*FOVHeightAngle)*hypoLower
    hypoTop = cam_height/(math.cos(viewingAngle+(0.5*FOVHeightAngle)))
    trapTop = math.tan(0.5*FOVHeightAngle)*hypoTop
        ## Coordinate in this order.
        ## x4,y2 ------------ x3,y2
        ##   |    (x4+x3)/2    |
        ##    |              |
        ## x2,y1 ---------- x1,y1
    x1 = float(cameraX + trapBottom)
    x2 = float(cameraX - trapBottom)
    x3 = float(cameraX + trapTop)
    x4 = float(cameraX - trapTop)
    y1 = float(cameraY + cameraToBottom)
    y2 = float(cameraY + cameraToTop)
    polyabc = Polygon(((x4,y2),(x3,y2),(x1,y1),(x2,y1)))
    PolyRotate = rotate(polyabc,bearingRad,cam_geom,use_radians=True)

    ## operation to join floorplan with the floor print
    PolyRotate = floorplanPoly.intersection(PolyRotate).convex_hull
    PolyRotateB = ReformBackShape(bearingRad,PolyRotate,x2,x1,y1) ## Rotate and adjust the polygon back to 4 corner
    polyText = PolyRotateB.wkt
    return polyText

db="osi_social_db"
dbuser="postgres"
dbpassword=""
dbhost="192.168.8.12"
dbport="5432"

## Load data from postgres
db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

## extract the floor plan to compare
cursor = db.cursor()
cursor.execute("""select geom from "osi_office" where name = 'floor';""") ## <== get the floor from the floor plan
floorPlan, = cursor.fetchone()
floorplanPoly = wkb.loads(floorPlan,hex=True)  ## convert the floor geom


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
        polyText = CreateFixedFootprint(view_angle,sensorWidth,sensorHeight,focusLength,bearing,cameraX,cameraY)
        polyFHolder = []
        polyText=str(polyText).replace("POLYGON ((","")
        polyText=str(polyText).replace("))","")
        polytextList = polyText.split(",")
        for data in polytextList:
            cLEANstr = str(data).lstrip(" ")
            splitstr = str(cLEANstr).split(" ")
            floatContent = [float(digit) for digit in splitstr]
            polyFHolder.append(floatContent)

        print polyFHolder

        # CheckFootprintExist = """Select count(uid) from office_footprint where uid = '%s';"""
        UpdateStatement = """update osi_camera
                                set footprint_str = '%s'
                            where camera_uid = '%s';"""


        cursor.execute(UpdateStatement % (str(polyFHolder),camera_UID))
        db.commit()



    elif cameraType == "DOME":

        polyTextdOME = CreateDOMEFootprint(view_angle,sensorWidth,sensorHeight,focusLength,bearing,cameraX,cameraY)
        # polystarement = "ST_GeomFromText('"+polyTextdOME+"',3857)"
        polyHolder = []
        polyTextdOME=str(polyTextdOME).replace("POLYGON ((","")
        polyTextdOME=str(polyTextdOME).replace("))","")
        polytextList = polyTextdOME.split(",")
        for data in polytextList:
            cLEANstr = str(data).lstrip(" ")
            splitstr = str(cLEANstr).split(" ")
            floatContent = [float(digit) for digit in splitstr]
            polyHolder.append(floatContent)

        print polyHolder

        # CheckFootprintExist = """Select count(uid) from office_footprint where uid = '%s';"""
        # InsertStatement = """insert into office_footprint(uid,geom) values('%s',%s)"""
        UpdateStatement = """update osi_camera
                                set footprint_str = '%s'
                            where camera_uid = '%s';"""
        print "UpdateStatement: "+str(UpdateStatement)

        cursor.execute(UpdateStatement % (str(polyHolder),camera_UID))

        db.commit()


    else:
        pass




