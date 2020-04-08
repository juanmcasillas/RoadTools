#from polar.gpxtoolbox import *
#from polar.mapper import *
from gpxpy import geo
import sys
import math
import numpy as np
from math import factorial


class GPXOptimizer:
    def __init__(self):
        self.st_total_points = 0
        self.st_near_points = 0
        self.st_straight_points = 0
        self.st_final_points = 0
        self.st_stopped_points = 0

        self.coef_near = 1.0
        self.coef_stopped_low = 1.0
        self.coef_stopped_high = 2.5
        self.coef_angle = 2.6
        self.coef_distance_low = 11
        self.coef_distance_high = 12
        self.coef_distance_delta = 4.5
        self.coef_near_angle = 3


        # hi res
        #self.coef_near = 0.5
        #self.coef_stopped_low = 1.0
        #self.coef_stopped_high = 2.5
        #self.coef_angle = 2.6
        #self.coef_distance_low = 4
        #self.coef_distance_high = 4
        #self.coef_distance_delta = 4
        #self.coef_near_angle = 2


    def Print_stats(self):
        print("-" * 79)
        print("Optimizer Stats")
        print("-" * 79)
        
        print("Total Points:", self.st_total_points)
        print("Near Points:", self.st_near_points)
        print("Straight Points:", self.st_straight_points)
        print("Final Points:", self.st_final_points)
        print("Stopped Points (d<1.0):", self.st_stopped_points)
        if self.st_total_points != 0:
            print("Save %3.2f %%" % float(100 - (self.st_final_points*100.0 /  self.st_total_points)))


    def Optimize(self,points,keep_points=False):

        if len(points)==0:
            return points
        
        self.st_total_points = len(points)

        if keep_points:
            [setattr(point,'keep',True) for point in points]
        
        p = self._optimize_straight_segments(points,keep_points)
        p = self._optimize_h_triangle(p,keep_points)
        p = self._optimize_stopped_points(p,keep_points)

        self.st_final_points = len(p)
        return p

    def _optimize_stopped_points(self, points,keep_points=False):

        # for "stopped" points, create an average, and remove those points that are in the same place.
        # if not, replicate the same point various times.
        
        tdata = [points[0]]
        for i in range(len(points)):
            
            p = points[i]
            if not p.time:
                continue
           
            # calculate some metrics.
            p.time_d = 0.0
            p.distance_d = 0.0
            p.elevation_d = 0.0
            p.speed = 0.0
           
            if i > 0:
                q = points[i-1]
                
                p.time_d      = p.time - q.time
                p.distance_d  = geo.length_2d([p, q]) #distance_2d #gpxpy.geo.distancePoints3D
                p.elevation_d = p.elevation - q.elevation
                p.speed       = 0.0
                if p.distance_d > 0.0 and p.time_d.total_seconds() > 0:
                    p.speed       = (p.distance_d / p.time_d.total_seconds()) * 3.6 # km/h
                
       

                # remove "stopped" points. No fully fixed.
                if p.distance_d > self.coef_stopped_low and p.speed > self.coef_stopped_high:
                    tdata.append(p)
                    #if p.speed < 5.0:
                        #print i, p.speed, p.time_d, p.distance_d, p.elevation_d
                else:
                    if keep_points:
                        p.keep = False
                        tdata.append(p)        
                    self.st_stopped_points +=1

                   
        tdata.append(points[i])
        return tdata


    def _optimize_straight_segments(self, points,keep_points=False):

        # remove points, if they are in a line.
        newlist = []

        i = 0

        while i < len(points)-1:

            j = i+2
            if j > len(points)-1: break

            p0 = points[i]
            p1 = points[i+1]    #next
            p2 = points[j]      # far item

            while j < len(points)-1:

                distance = geo.length_2d([ p0, p1] )
                distance2 = geo.length_2d([ p1, p2] )



                alpha = geo.bearing(p0, p1)
                beta = geo.bearing(p0, p2)

                delta = math.fabs(beta-alpha)

                # 1.4
                # 1.3
                #if distance > 0 and distance2 > 0: print delta/distance, delta/distance2
                # running is a different thing .... the lap time is greater, so...

                # with 2.5 an 2.6 down works fine.


                if delta < self.coef_distance_delta and distance < self.coef_distance_low  and distance2 < self.coef_distance_high:   # some caveats with long distances (in the second point)
                    self.st_straight_points += 1

                    if keep_points:
                        p0.keep = False
                        newlist.append(p0) 
                    
                    p1 = points[j]
                    j += 1
                    p2 = points[j]
                    continue

                else:
                    newlist.append(p0)
                    # jump two points if angle is small enough
                    if delta > self.coef_angle:
                        i +=1
                    else:
                        i =j
                    break


            if j >= len(points)-1:
                break

        newlist.append(points[-1])
        return newlist

    def _optimize_h_triangle(self, points,keep_points=False):

        # calculate line, distance, and so on.
        newlist = []

        i = 0
        while i < len(points)-2:

            p0 = points[i]
            p1 = points[i+1]    #next
            p2 = points[i+2]    #far next

            a =  geo.length_2d([ p1, p0] )
            b =  geo.length_2d([ p2, p1] )
            c =  geo.length_2d([ p2, p0] )

            s = (a + b + c) / 2.0

            sa = (s - a)
            sb = (s - b)
            sc = (s - c)


            distance = 0.0
            if s*sa*sb*sc >= 0.0 and c != 0.0:
                distance = (2.0 / c) * math.sqrt(s*sa*sb*sc)

            alpha = geo.bearing(p0, p1)
            beta = geo.bearing(p0, p2)
            delta = math.fabs(beta-alpha)


            #print("D/d:", distance, geo.length_2d([ p2, p0] ), geo.length_2d([ p2, p1] ), alpha, beta, beta-alpha)

            # in meters
            newlist.append(p0)
            
            if distance <= self.coef_near and delta < self.coef_near_angle:
                # skip the middle point
                self.st_near_points += 1
                if keep_points:
                    p = points[i+1]
                    p.keep = False
                    newlist.append(p)
                i += 2
            else:
                i += 1

        # add the last point
        #newlist.append(points[-1])
        return newlist

    # deprecated and test methods


def savitzky_golay(y, window_size, order, deriv=0, rate=1):


    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except (ValueError, msg):
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')


def CHECK_LINE():

    points = [ geo.Location(1.0,1.0),  geo.Location(3.0, 2,0),  geo.Location(4.0,4.0),  geo.Location(5.0,5.0),  geo.Location(6.0,6.0) ]

    gpx_optmizer = GPXOptimizer()
    opt_points = gpx_optmizer.Optimize(points)
    gpx_optmizer.Print_stats()

    sys.exit(0)
