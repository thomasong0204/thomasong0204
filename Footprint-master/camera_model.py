import numpy
import psycopg2


## get the camera rotation matrix
## start with the camera model

###########################################
## x = K[R t] X
## x: Image Coordinates: (u,v,1)
## K: Intrinsic Matrix (3x3)
## R: Rotation (3x3) 
## t: Translation (3x1)
## X: World Coordinates: (X,Y,Z,1)
###########################################


## Convert from older work done (Geolocation.js)





# Footprint = [
# 		[x3, ((x4+x3)/2), x4, ((x3+x2)/2), ((x4+x3)/2),((x4+x1)/2),  x2,((x2+x1)/2),x1],
#     [y2,y2,y2, ((y1+y2)/2), ((y1+y2)/2), ((y1+y2)/2), y1,y1,y1],[1,1,1,1,1,1,1,1,1]]

def getCameraFOOTPrint(TVgrid):
    db="osi_social_db"
    dbuser="postgres"
    dbpassword=""
    dbhost="192.168.8.12"
    dbport="5432"

    ## Load data from postgres
    db = psycopg2.connect(database=db, user=dbuser, password=dbpassword, host=dbhost, port=dbport)

    ## extract the floor plan to compare
    cursor = db.cursor()
    cursor.execute("""select footprint_str,camera_uid from "osi_camera" ;""") ## <== get the floor from the floor plan
    footprintA = cursor.fetchall()
    for (fP,uid) in footprintA:
        print fP
        print uid





if __name__ == '__main__':
    ## Screen resolution related
    screen_resolution=[1080,720]
    midX = screen_resolution[0]/2
    midY = screen_resolution[1]/2

    TVgrid = [
		[0,midX,screen_resolution[0], 0,midX,screen_resolution[0], 0,midX,screen_resolution[0]], 
		[0,0,0,midY,midY,midY,screen_resolution[1],screen_resolution[1],screen_resolution[1]], 
		[1,1,1,1,1,1,1,1,1]]

    getCameraFOOTPrint(TVgrid)




