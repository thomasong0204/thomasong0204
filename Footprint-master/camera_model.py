import numpy as np
import psycopg2
import ast
import math

from shapely import wkb
from shapely.geometry import Polygon
from shapely.affinity import rotate
from shapely.wkt import dumps


## get the camera rotation matrix
## start with the camera model

## input xy position of the screen and get the realworld coordinate in return
def realworldXY(ScreenX,ScreenY,transformM):

    ## need to include the shearing matrix into
    a = transformM[0]
    b = transformM[1]
    c = transformM[2]
    d = transformM[3]
    e = transformM[4]
    f = transformM[5]
    g = transformM[6]
    h = transformM[7]

    realX = (a*ScreenX+b*ScreenY+c)/(g*ScreenX+h*ScreenY+1)
    realY = (d*ScreenX+e*ScreenY+f)/(g*ScreenX+h*ScreenY+1)


    return (realX,realY)

## Store the transformation
def Store_transformM(transformM,cam_uid):
    db="osi_social_db"
    dbuser="postgres"
    dbpassword=""
    dbhost="192.168.8.12"
    dbport="5432"

    ## Load data from postgres
    db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

    ## extract the floor plan to compare
    cursor = db.cursor()
    UpdateStatement = """update osi_camera
                            set transformation_matrix = %s
                            where camera_uid = %s;"""
    act_sql = cursor.mogrify(UpdateStatement, (str(transformM), cam_uid))
    print act_sql
    cursor.execute(act_sql)
    db.commit()


## get camera footprint
def getCameraFOOTPrint():
    db="osi_social_db"
    dbuser="postgres"
    dbpassword=""
    dbhost="192.168.8.12"
    dbport="5432"

    ## Load data from postgres
    db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

    ## extract the floor plan to compare
    cursor = db.cursor()
    cursor.execute("""select * from "osi_camera";""") ## <== get the floor from the floor plan
    footprintA = cursor.fetchall()
    
    del cursor
    del db
    return (footprintA)


def reconstruct9Point(footprint2):
    ## Coordinate in this order.
    ## x4,y2 ------------ x3,y2
    ##   |    (x4+x3)/2    |
    ##    |              |
    ## x2,y1 ---------- x1,y1
    x4,y2 = footprint2[0]
    x3,y2 = footprint2[1]
    x1,y1 = footprint2[2]
    x2,y1 = footprint2[3]
    ## reconstruct the footprint from 4 points to 9 points
    ReconstructFP = [[x4, ((x4+x3)/2), x3, ((x4+x2)/2), ((x4+x3)/2),((x3+x1)/2),x2,((x2+x1)/2),x1],
    [y2,y2,y2, ((y1+y2)/2), ((y1+y2)/2), ((y1+y2)/2), y1,y1,y1]]
    return (ReconstructFP,y1,y2,x4,x3)


def transformationMatrix(footprint,TVgrid):
    ## drop the element to 4 instead of 5 received in the array.
    ## use the example from
    ##  http://www.corrmap.com/features/homography_transformation.php
    ##  this example works in python

    footprint2 = footprint[0:4]
    
    ## x4,y2 ------------ x3,y2
    ##   |    (x4+x3)/2    |
    ##    |              |
    ## x2,y1 ---------- x1,y1
    ##  Big x and y in the sample
    x4,y2 = footprint[0]
    x3,y2 = footprint[1]
    x1,y1 = footprint[2]
    x2,y1 = footprint[3]
 

    ## TVgrid POINTS
    ## small x and y in the example
    TX4,TX3,TX1,TX2 = TVgrid[0]
    TY4,TY3,TY1,TY2 = TVgrid[1]

    matrixA = np.array([[TX4,TY4,1,0,0,0,-TX4*x4,-TY4*x4],
                [TX3,TY3,1,0,0,0,-TX3*x3,-TY3*x3],
                [TX1,TY1,1,0,0,0,-TX1*x1,-TY1*x1],
                [TX2,TY2,1,0,0,0,-TX2*x2,-TY2*x2],
                [0,0,0,TX4,TY4,1,-TX4*y2,-TY4*y2],
                [0,0,0,TX3,TY3,1,-TX3*y2,-TY3*y2],
                [0,0,0,TX2,TY2,1,-TX2*y1,-TY2*y1],
                [0,0,0,TX1,TY1,1,-TX1*y1,-TY1*y1]])

    ## output matrix in real world coordinate system
    O_matrix = np.array([x4,x3,x1,x2,y2,y2,y1,y1])
    ## use python matrix solver to get the transformation matrix.
    TMatrix = np.linalg.solve(matrixA,O_matrix)

    return TMatrix
    
    

if __name__ == '__main__':
    ## Screen resolution related
    ## obtain the resolution from json
    screen_resolution=[1920,1200]
    midX = screen_resolution[0]/2
    midY = screen_resolution[1]/2

    sX = 1194
    sY = 879

    objectPixelH = 310

    ## 4 points
    TVgrid = [[0,screen_resolution[0],screen_resolution[0], 0],
		[0,0,screen_resolution[1],screen_resolution[1]]]

    for cameras in getCameraFOOTPrint():
        
        cam_uid = cameras[2]
        cam_height = cameras[8]
        camerapoint = wkb.loads(cameras[0],True)
        camX = camerapoint.xy[0]
        camY = camerapoint.xy[1]

        ## Check if footprint exist
        if cameras[20] is not None:
            footprint =  ast.literal_eval(cameras[20])
            # Get_view_angle = getCameraFOOTPrint()[1]

            ## transformation matrix
            transformM = transformationMatrix(footprint,TVgrid)
            # print transformM

            Store_transformM(transformM,cam_uid)

            ## locationPosition (x,y)
            a1 = [[sX,sY],[sX,sY+objectPixelH]]
            CollectX = []
            CollectY = []
            for pos in a1:
                xpos = pos[0]
                ypos = pos[1]
                realx,realy= realworldXY(xpos,ypos,transformM)
                CollectX.append(realx)
                CollectY.append(realy)

            objDist = math.sqrt((CollectY[0]-CollectY[1])**2 + (CollectX[0]-CollectX[1])**2)
            distanceToCamera = math.sqrt((CollectY[0]-camY)**2 + (CollectX[0]-camX)**2)
            
            objectHeight = (cam_height*objDist)/distanceToCamera
            print objectHeight

    # print "screen to real world=>" + str(resultRW)




