#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ///////////////////////////////////////////////////////////////////////////
#
# Read a GPX file, and build a road. Return the data in the normalized
# OpenGL vertexData structure
#
# ///////////////////////////////////////////////////////////////////////////

import sys
import gpxpy
import gpxpy.gpx

import pyproj
import numpy as np
import os
import math
import pyGLLib
np.set_printoptions(precision=4, floatmode="fixed", suppress=True)

from gpx_optimizer import GPXOptimizer, savitzky_golay

def test_gpx(fname):

    # a = [1, 1, 1, 
    #      2, 8, 2, 
    #      10, 10, 3,
    #      15, 4, 9 ]

    # x = BoundingBox()
    # print(np.array(a).reshape(4,3))
    # a = x.calculate(a, offset=False, interp=((0,150), (0,100), (0,1)))
    # print("---")
    # print(np.array(a).reshape(4,3))
    # print(x)
    # print(x.coords)

    loader = GPXLoader(fname)
    points = loader.load() 

    #
    # get the points, move then to the top left origin, and then,
    # map the vectors to the new coordinate space.
    #
    # bb = BoundingBox()
    # points = bb.calculate(points, offset=True, interp=((0,10), (0,10), (0,5)))
    # print(points)
    # import matplotlib.pyplot as plt
    # d = np.array(points).reshape(int(len(points)/3),3)
    # x = d[:,[0]]
    # y = d[:,[1]]
    # plt.plot(x,y, linestyle="", marker="o")
    # plt.show()

    #
    # get the points, move then to the top left origin, and then,
    # map the vectors to the new coordinate space.
    #
    bb = BoundingBox()
    points = bb.calculate(points, offset=True, interp=((0,10), (0,10), (0,5)))

    roadgen = RoadGenerator(points)
    vertex = roadgen.build(1)

    draw(vertex)

# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////
class ProjectionMapper:
    """
    project a WSG84 to UTM
    z, l, x, y = project((point.longitude, point.latitude))
    """

    def __init__(self):
        self._projections = {}

    def zone(self,coordinates):
        if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
            return 32
        if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
            if coordinates[0] < 9:
                return 31
            elif coordinates[0] < 21:
                return 33
            elif coordinates[0] < 33:
                return 35
            return 37
        return int((coordinates[0] + 180) / 6) + 1


    def letter(self,coordinates):
        return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]

    def project(self,coordinates): # lon, lat
        z = self.zone(coordinates)
        l = self.letter(coordinates)
        if z not in self._projections:
            self._projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
        x, y = self._projections[z](coordinates[0], coordinates[1])
        if y < 0:
            y += 10000000
        return z, l, x, y

    def project_2(self, lon, lat):
        
        myProj = pyproj.Proj("+proj=utm +zone=30T, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
        UTMx, UTMy = myProj(lon, lat)
        #print(lat, lon, UTMx, UTMy)
        return (UTMx, UTMy)

    def unproject(self, z, l, x, y):
        if z not in self._projections:
            self._projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
        if l < 'N':
            y -= 10000000
        lng, lat = self._projections[z](x, y, inverse=True)
        return (lng, lat)


# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////
class GPXLoader:
    def __init__(self, fname=None, optimize=False):
        self.fname = fname
        self.optimize = optimize

    def load(self,fname=None):
        f = fname or self.fname
        if f is None:
            raise ValueError("GPX file is None")
        if not os.path.exists(f):
            raise RuntimeError("GPX file %s not found" % f)

        gpx_file = open(f, 'r')
        gpx_data = gpxpy.parse(gpx_file)

        points = []
        pm = ProjectionMapper()

        # call my optimizer (remove contiguous points)
        points = []
        for track in gpx_data.tracks:
            for segment in track.segments:
                points += segment.points

        if self.optimize:
            gpx_optmizer = GPXOptimizer()
            opt_points = gpx_optmizer.Optimize(points)
            gpx_optmizer.Print_stats()
            points = opt_points
            elevs = []
        ret_points = []
        
        for point in points:
            z, l, x, y = pm.project((point.longitude, point.latitude))
            #x,y = pm.project_2(point.longitude, point.latitude)
            point.x = x
            point.y = y
            ret_points += [x, y, point.elevation]
            self.optimize and elevs.append(point.elevation)
        
        if self.optimize:
            #smoothed_elevations = np.array(savitzky_golay( np.array(elevs) , 135, 5))
            smoothed_elevations = savitzky_golay( np.array(elevs) , 11, 5)
            #idx = np.arange(0,44)
            #import matplotlib.pyplot as plt
            #plt.plot(idx,elevs[0:44])
            #plt.plot(idx,smoothed_elevations[0:44])
            #plt.show()
            ret_points = np.array(ret_points).reshape( int(len(ret_points)/3), 3)
            ret_points[:,2] = smoothed_elevations[0:len(elevs)]

        return(ret_points)


# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////
class BoundingBox(object):
    """
    A 2D bounding box
    """
    def __init__(self):
        pass

    def calculate(self, points, offset=False, interp=None, normals=False):
        """
        Compute the upright 2D bounding box for a set of
        2D coordinates in a (n,3) numpy array.

        You can access the bbox using the
        (minx, maxx, miny, maxy) members.
        """
        if isinstance(points,list):
            if not normals:            
                points = np.array(points).reshape(int(len(points)/3) ,3)
            else:
                points = np.array(points).reshape(int(len(points)/6) ,6)

        self.minx = np.min(points[:,[0]]) # X
        self.maxx = np.max(points[:,[0]]) # X
        
        self.miny = np.min(points[:,[1]]) # Y
        self.maxy = np.max(points[:,[1]]) # Y
        
        self.minz = np.min(points[:,[2]]) # Z
        self.maxz = np.max(points[:,[2]]) # Z

        # offset the data to 0 (top, left)
        if offset:
            if normals:
                x,y,z = self.center
                points = points - [ x, y, z, 0.0, 0.0, 0.0]
            else:
                points = points - self.center

            self.minx_o = self.minx
            self.maxx_o = self.maxx
            self.miny_o = self.miny
            self.maxy_o = self.maxy
            self.minz_o = self.minz
            self.maxz_o = self.maxz

            # recompute new values
            self.minx = np.min(points[:,[0]]) # X
            self.maxx = np.max(points[:,[0]]) # X
           
            self.miny = np.min(points[:,[1]]) # Y
            self.maxy = np.max(points[:,[1]]) # Y
            
            self.minz = np.min(points[:,[2]]) # Z
            self.maxz = np.max(points[:,[2]]) # Z
        
        # interpolate the data to the new space
        if interp is not None:
            #
            # sighly open the range to avoid bad interpolation of decimals
            # due precision           
            #
            #print(points)
            D = 0.1
            x = np.interp(points[:,[0]], (self.minx-D, self.maxx+D), interp[0])
            y = np.interp(points[:,[1]], (self.miny-D, self.maxy+D), interp[1])
            z = np.interp(points[:,[2]], (self.minz-D, self.maxz+D), interp[2])   
            if normals:
                a = points[:,[3]]
                b = points[:,[4]]
                c = points[:,[5]]
                points = np.column_stack((x,y,z,a,b,c))
            else:
                points = np.column_stack((x,y,z))
    
  

        return points.flatten()

    @property
    def width(self):
        """X-axis extent of the bounding box"""
        return self.maxx - self.minx

    @property
    def height(self):
        """Y-axis extent of the bounding box"""
        return self.maxy - self.miny

    @property
    def area(self):
        """width * height"""
        return self.width * self.height

    @property
    def aspect_ratio(self):
        """width / height"""
        return self.width / self.height

    @property
    def center(self):
        """(x,y) center point of the bounding box"""
        # minz to offset the heights to 0
        mz = (self.maxz-self.minz)/2
        #mz = self.minz
        return (self.minx + self.width / 2, self.miny + self.height / 2, mz)

    @property
    def max_dim(self):
        """The larger dimension: max(width, height)"""
        return max(self.width, self.height)

    @property
    def min_dim(self):
        """The larger dimension: max(width, height)"""
        return min(self.width, self.height)

    @property
    def coords(self):
        """The larger dimension: max(width, height)"""
        a = (self.minx, self.miny, self.minz)
        b = (self.maxx, self.maxy, self.maxz)
        return (a, b)

    def __repr__(self):
        return "BoundingBox({}, {}, {}, {}, {}, {})".format(
            self.minx, self.maxx, self.miny, self.maxy, self.minz, self.maxz)


def V_M(U):
    "calculate the modulus"
    module = np.sqrt( math.pow(U[0],2) + math.pow(U[1],2) + math.pow(U[2],2) )
    return module

def V_U(U):
    "calculate unitary vector"
    module = V_M(U)
    if module == 0.0:
        print("Offending vector: ",U)
        raise RuntimeError()
    U = U/module  
    return U  

def calc_normal_from_triangle(triangle):
    
    normals = [[0.0,0.0,0.0]]*3
    Q,R,S = triangle
    
    if np.array_equal(Q,R) or np.array_equal(Q,S):
        print("Same vectors detected: ",Q,R,S)
        return normals


    #first vertex
    QR = R-Q
    QS = S-Q
    normals[0] =  V_U(list(np.cross(QR,QS))).flatten()

    #second vertex
    RS = S-R
    RQ = Q-R
    normals[1] = V_U(list(np.cross(RS,RQ))).flatten()

    #third vertex
    SQ = Q-S
    SR = R-S
    normals[2] = V_U(list(np.cross(SQ,SR))).flatten()
    return normals   

def remove_duplicates(points):
    #https://stackoverflow.com/questions/39541276/take-unique-of-numpy-array-according-to-2-column-values
    #shape the points to array
    "remove duplicate rows"
    dt = points.dtype.descr * points.shape[1]    
    points_view = points.view(dt)
    points_uniq, points_idx = np.unique(points_view, return_index=True)
    points = points[points_idx]
    return(points)

class RoadGenerator(object):
    def __init__(self, points):
        # build a [len,3] matrix
        self.interp_range = ( (-1,1), (-1,1), (0,10) ) # z big reduces the elev exageration 10 for bike, 2 for run.
        self.bb = BoundingBox()

        self.points = self.bb.calculate(points, offset=True)
        self.points = np.array(self.points).reshape(int(len(self.points)/3),3)
        #self.points = remove_duplicates(self.points)
        
  
        #self.f32sz = np.dtype(np.float32).itemsize
    
    def normalize(self, points):
        bb = BoundingBox()
        points = bb.calculate(points, interp=self.interp_range, normals=True)
        return(points)

    def add_perpendicular(self, distance):
        i = 0
        vertex = []
        for i in range(len(self.points)):
            if i == len(self.points)-1:
                # last point
                P = self.points[-1]
                Q = self.points[-2]
            else:
                P = self.points[i]
                Q = self.points[i+1]
            
            # remove the height for now (Z)
            #P[2] = Q[2] = 0.0
            
            PQ = Q-P
   
            #PQ_U = V_U(PQ)
            # this is the NORMAL vector 
            #T1 = np.array(( -PQ[1], 0.0, PQ[0])) * distance
            #T2 = np.array(( PQ[1], 0.0, -PQ[0])) * distance
            if V_M(PQ) < 0.01:          
                print("points are too near, skipping them")
                continue
            if PQ[0] == PQ[1] == 0.0:            
                print("vector is the same. Skipping (maybe different altitude)")
                continue

            #print("distance PQ: %3.3f, %3.3f, %3.3f (eD: %3.3f)" % (V_M(PQ),P[2],Q[2],Q[2]-P[2]))
            
            #T1 = V_U(np.array(( -abs(PQ[1]),  abs(PQ[0]), PQ[2]))) * distance
            #T2 = V_U(np.array((  abs(PQ[1]), -abs(PQ[0]), PQ[2]))) * distance           

            # this uses the 3D position of the point, creating a non-leveled road
            #T1 = V_U(np.array(( -abs(PQ[1]),  abs(PQ[0]), abs(PQ[2])))) * distance
            #T2 = V_U(np.array((  abs(PQ[1]), -abs(PQ[0]), abs(PQ[2])))) * distance            
            # this creates a leveled road.
            T1 = V_U(np.array(( -abs(PQ[1]),  abs(PQ[0]), 0.0))) * distance
            T2 = V_U(np.array((  abs(PQ[1]), -abs(PQ[0]), 0.0))) * distance            
  

            T1 = P + T1 
            T2 = P + T2 
            vertex += [ T1, P, T2]
 
        return vertex
        
    def build(self, distance):
        # T1, P, T2
        # Q1, Q, Q2
        # ....
        
        #7587
        print("%d points loaded" % len(self.points))

        #self.points=self.points[0:30]
        #print(self.points)
        # import matplotlib.pyplot as plt
        # d = self.points
        # x = d[:,[0]]
        # y = d[:,[1]]
        # plt.scatter(x,y)
        # plt.show()  

        triangles = []
        quads = self.add_perpendicular(distance)
 
        i=0
        # skip last polygon.
        while i < len(quads)-5:
            #print(i, triangles)
            #print(quads)
            Q = quads[i+2]
            R = quads[i]
            S = quads[i+5]
            nQ,nS,nR = calc_normal_from_triangle((Q,S,R))
            triangles += [ Q,nQ, R, nR, S,nS ]
           
            Q = quads[i+5]
            R = quads[i]
            S = quads[i+3]
            nQ,nS,nR  = calc_normal_from_triangle((Q,S,R))
            triangles += [ Q,nQ, S,nS, R, nR ]

            i = i+3
    

      
        x = np.array(triangles).flatten()
        x = np.array(x).reshape(int(len(x)/6),6)
    
        

        # swap Y by Z (data and normals)
        x.T[[1, 2]] = x.T[[2, 1]]
        x.T[[4, 5]] = x.T[[5, 4]]
        
        x = self.normalize(x)    

        return np.array(x.flatten(),dtype=np.float32)

 

# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////
def draw(points):
    import matplotlib.pyplot as plt
    d = np.array(points).reshape(int(len(points)/3),3)
    x = d[:,[0]]
    y = d[:,[1]]
    plt.plot(x,y, linestyle="",marker="o")
    plt.show()    


class GLRoad(pyGLLib.object.GLObjectBaseNormal):
    
    def __init__(self, fname, distance=5, optimize=False):
        super().__init__()
        self.fname = fname
        self.distance = distance
        self.optimize = optimize

    def load_model(self):
        loader = GPXLoader(self.fname, self.optimize)
        points = loader.load() 

        # points = [
        #      -0.4, 0.0, -0.4,
        #       0.0, 0.0, 0.0,
        #       0.4, 0.0, 0.4, ##dup!
        #       0.4, 0.0, 0.4
        #  ]
        # points = np.array(points).reshape(4,3)


       
        roadgen = RoadGenerator(points)
        self.vertexData = roadgen.build(self.distance)

        #print(np.array(self.vertexData).reshape(int(len(self.vertexData)/6),6))

        #self.vertexData = self.vertexData[0:6*3]
        #self.vertexData = self.vertexData[6*3:6*3*2]
        #self.vertexData = self.vertexData[6*3*2:6*3*3]
        #self.vertexData = self.vertexData[6*3*3:]
        #self.triangles = len(self.vertexData)/(3*6)

        # self.vertexData = np.array([
        #     -0.5,  0.5,  0.,   0.,   0.,  -1., 
        #     -0.5, -0.5,  0.,   0.,   0.,  -1., 
        #      0.5, -0.5,  0.,   0.,   0.,  -1., 
        #      0.5, -0.5,  0.,   0.,  -0.,   1., 
        #      0.5,  0.5,  0.,   0.,   0.,   1., 
        #     -0.5, -0.5,  0.,   0.,   0.,   1., 
        # ],dtype=np.float32)
    
        
 

if __name__ == "__main__":
    test_gpx(sys.argv[1])



# <trkpt lat="40.3607123997" lon="-4.39237592742">
# LAT: 40,360712
# LON: -4,392376
# UTM: 
# EASTING  381773.05,    |379616.8156
# NORTHING: 4468724.38   |4467918.9641 
# ZONE: 30T