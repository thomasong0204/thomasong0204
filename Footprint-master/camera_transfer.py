import math
import numpy
import psycopg2
from shapely import wkb
from shapely.geometry import Polygon
from shapely.affinity import rotate
from shapely.wkt import dump


def getCameraPT(cam_uid):
    ## using numpy for matrix.abs
    db="osi_social_db"
    dbuser="postgres"
    dbpassword=""
    dbhost="192.168.8.12"
    dbport="5432"

    ## Load data from postgres
    db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

    ## extract the floor plan to compare
    cursor = db.cursor()
    sqlstring = """select geom,bearing from osi_camera where camera_uid = '%s';"""
    
    cursor.execute(sqlstring % (cam_uid)) ## <== get the geometry of the camera
    camera = cursor.fetchone()
    print "camera: "+str(camera)

    return camera

## get distance from point to camera
def pointdistance():


    return


## using numpy for matrix.abs
db="osi_social_db"
dbuser="postgres"
dbpassword=""
dbhost="192.168.8.12"
dbport="5432"

## Load data from postgres
db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

## extract the floor plan to compare
cursor = db.cursor()
cursor.execute("""select * from "office_footprint";""") ## <== get the floor from the floor plan
footprints = cursor.fetchall()

## proceed to extract the centroid and coordinates from each footprint.
for fp in footprints:
    uid,fpString = fp
    readfppolygon = wkb.loads(fpString,hex=True)

    ## get the camera point and rotation
    camera,rotation = getCameraPT(uid)
    cameraPT = wkb.loads(camera,hex=True)
    cameraPTX,cameraPTY = cameraPT.xy   ## obtain the xy of the camera.

    ## get the centroid of the footprint.
    ([centroidX],[centroidY]) = readfppolygon.centroid.xy
    (polyX,polyY)= readfppolygon.boundary.coords.xy
    ## this is the centre point of the polygon
    ## this will be used in the matrix
    

    ## calculate the distance from camera to centroid
    StraightD = readfppolygon.centroid.distance(cameraPT)


    print StraightD
    # print uid
    print "*"*50


