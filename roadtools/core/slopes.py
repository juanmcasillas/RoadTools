import sys

import datetime
import time
import os.path
import gpxpy
import gpxpy.gpx
from gpxtoolbox import GPXItem
import argparse
import math
from gpx_optimizer import GPXOptimizer, savitzky_golay

class SlopeManager:
    def __init__(self, distance_gap=100.0):
        self.distance_gap = distance_gap
        self.fname = None
        self.gpx = None
        self.points = None
               
        #[n,m] -> [counter,weight]
        self.errors = { 'distance': { 'counter': 0, 'weight': 0.5},  #distance == 0
                        'stopped':  { 'counter': 0, 'weight': 0.5},  #speed = 0
                        'slope':    { 'counter': 0, 'weight': 1.0},  #><45
                        'speed':    { 'counter': 0, 'weight': 1.2}   #>120
                      }
        
 
        
        self.tdata_tpl = """<tr class='%s'>
                    <td class='trackanalysis_orig'>%d</td>
                    <td class='trackanalysis_orig'>%s</td>
                    <td class='trackanalysis_orig'>%s</td>
                    
                    <td class='trackanalysis_orig'>%s</td>
                    <td class='trackanalysis_orig'>%3.2f</td>
                    
                    <td class='trackanalysis_calc'>%3.2f</td>
                    <td class='trackanalysis_calc'>%3.2f</td>
                    <td class='trackanalysis_calc'>%3.2f</td>
                    
                    
                    <td class='trackanalysis_delta'>%3.2f</td>
                    <td class='trackanalysis_delta'>%3.2f</td>
                    <td class='trackanalysis_delta'>%s</td>
                    <td class='trackanalysis_delta'>%3.2f</td>
                    <td class='trackanalysis_delta'>%3.2f</td>
                    <td class='trackanalysis_delta'>%3.2f</td>
                     
                    <td class='trackanalysis_delta'>%s</td>
                    <td class='trackanalysis_delta'>%s</td>
                    
                    </tr>
                    """
                    
        self.page_tpl = """
        <html>
        <head>
        <style>
            @import url('https://fonts.googleapis.com/css?family=Roboto');
            
            body {
                font-family: 'Roboto', sans-serif;
                /*font-family:arial, verdana, helvetica, sans-serif;*/
                font-size:12px;
                cursor:default;
                background-color:#FFFFFF
            }

            table.trackanalysis  {
                width: auto;
                margin: 0px;
                border-collapse: collapse;
                text-align: right;
            }
            
            table.trackanalysis tr td  {
               border: 1px black solid;
               padding-left: 2px;
               padding-right: 2px;
            }
            
            tr.trackanalysis_head {
               background-color: #FAFAFA;
            }
            
            
            td.trackanalysis_orig {
               background-color: #80CF80;
            }
            
            td.trackanalysis_calc {
               background-color: #60AF60;
            }
            
            td.trackanalysis_delta {
               background-color: #8080CF;
            }
            
            tr.trackanalysis_bad td {
               background-color: #C04040;
            }
        </style>
        </head>
        <body>
         <table class="trackanalysis">
        <!--head -->
        <th>
        <tr class="trackanalysis_head">
        <td><b>#</b></td>
        <td><b>Latitude</b></td>
        <td><b>Longitude</b></td>
        <td><b>Time</b></td>
        <td><b>Elevation (m)</b></td>
       
        
        <td><b>Distance (m)</b></td>
        <td><b>Uphill (m)</b></td>
        <td><b>Downhill (m)</b></td>
        
        
        <td><b>ElevationD (m)</b></td>
        <td><b>DistanceD (m)</b></td>
        <td><b>TimeD </b></td>
        <td><b>Speed (km/h)</b></td>
        <td><b>Slope (%%)</b></td>
        <td><b>SlopeAvg (%%)</b></td>
        
        <td><b>Wrong Point?</b></td>
        <td><b>Required?</b></td>
        
        </tr>
        </th>
        
        %s
        
        </table>
        </body>
        """
        

    def __getitem__(self, key):
        return self.points[key]
    
    def __setitem__(self, key, value):
        
        self.points[key] = value
        return self.points[key]
    
    def __delitem__(self,key):
        return self.points.__delitem__(key)
    
    def len(self):
        return len(self.points)
        
    def LoadGPX(self, fname, optimize=False):
        self.fname = fname
        
        self.gpx = GPXItem()
        try:
            self.gpx.Load(self.fname)
            self.gpx.MergeAll()
            self.gpx = self.gpx.gpx # trick
            self.points = self.gpx.tracks[0].segments[0].points
            
            if optimize:
                gpx_optmizer = GPXOptimizer()
                opt_points = gpx_optmizer.Optimize(self.gpx.tracks[0].segments[0].points, keep_points=True)
                #opt_points = gpx_optmizer.Optimize(opt_points)
                gpx_optmizer.Print_stats()
                self.gpx.tracks[0].segments[0].points = opt_points
                self.points = self.gpx.tracks[0].segments[0].points
            
        except Exception as e:
            print("Error parsing file: %s: %s" % (self.fname, e))
            sys.exit(0)
            
        
            
    def LoadGPXFromString(self, gpx_str, fname='-'):
            self.gpx_fname = fname
            try:
                self.gpx = gpxpy.parse(gpx_str)
                while len(self.gpx.tracks)>0 and len(self.gpx.tracks[0].segments) > 1:
                    self.gpx.tracks[0].join(0,1)
                    
                self.points = self.gpx.tracks[0].segments[0].points
            except Exception as e:
                print("Error parsing GPX XML string: %s" % (e))
                sys.exit(0)

    def SetGPX(self, gpx, fname='-'):
        self.fname = fname
        self.gpx = gpx
        self.points = self.gpx.tracks[0].segments[0].points
        
    def SetGPXPoints(self, gpx_points, fname='-'):
        self.fname = fname
        self.gpx = None
        self.points = gpx_points
        
        
    def DumpPoints(self):
        data = self.GenerateHTML()
        s = self.page_tpl % data
        return s
        
    def Analyze(self):
            
        tdata = []
        for i in range(len(self.points)):
            
            p = self.points[i]
            
            if not p.time:
                continue
            
            
            
            
            
            p.stime =  p.time.strftime("%Y-%m-%d %H:%M:%S")
            
            # calculate some metrics.
            p.time_d = 0.0
            p.distance_d = 0.0
            p.elevation_d = 0.0
            p.uphill = 0.0
            p.downhill = 0.0
            p.distance = 0.0
            p.speed = 0.0
            p.slope = 0.0
            p.wrong = ""
            
            if not hasattr(p,'keep'):
                p.keep = True
            
            has_error = False
            
            if i > 0:
                q = self.points[i-1]
                
                p.time_d      = p.time - q.time
                p.distance_d  = gpxpy.geo.distancePoints3D(p, q)
                p.elevation_d = p.elevation - q.elevation
                p.distance    = q.distance + p.distance_d
                p.speed       = 0.0
                if p.distance_d > 0.0 and p.time_d.total_seconds() > 0:
                    p.speed       = (p.distance_d / p.time_d.total_seconds()) * 3.6 # km/h
                
                # slope
                p.slope       = gpxpy.geo.gradeslope(p.distance_d, p.elevation_d)
                
                
                if p.elevation_d > 0:
                    p.uphill   = q.uphill + p.elevation_d
                    p.downhill = q.downhill
                else:
                    p.downhill   = q.downhill + p.elevation_d
                    p.uphill     = q.uphill 
            
                # mark "errors"
                
                if p.distance_d == 0.0: 
                    has_error = True
                    p.wrong = "DistanceD==0.0"
                    self.errors['distance']['counter'] += 1
                
                if p.speed == 0.0: 
                    has_error = True
                    p.wrong = "speed==0.0"
                    self.errors['stopped']['counter'] += 1
                    
                if math.fabs(p.slope) > 45: 
                    has_error = True
                    p.wrong = "slope %3.2f" % p.slope
                    self.errors['slope']['counter']  += 1
                    
                if math.fabs(p.speed) > 120:  
                    has_error = True
                    p.wrong = "speed %3.2f" % p.speed
                    self.errors['speed']['counter']  += 1
                    
                
            tdata.append( (has_error, i, 
                          p.latitude, p.longitude, p.stime, p.elevation,
                          p.distance, p.uphill, p.downhill,
                          p.elevation_d, p.distance_d, p.time_d, p.speed,  p.slope, p.slope_avg,  p.wrong, p.keep) )
            
        
       
        
        
        return tdata
    
    
    def GenerateHTML(self):
            
        tdata = ""
        elements = self.Analyze()
        
        for e in elements:
            
            cssclasserr = ""
            if e[0] == True:
                cssclasserr = "trackanalysis_bad" 
                
            if e[-1] == False:
                cssclasserr = "trackanalysis_redundant"
                
            x = list(e)
            x[0] = cssclasserr
            e = tuple(x)
            
            l = self.tdata_tpl % e
            tdata += l
        
        return tdata
    
    
    def ComputeSlope(self):
        
        if len(self.points) == 0:
            return
    
        distance_incr = 0.0
        elevation_incr = 0.0
        
        for i in range(len(self.points)):
            p = self.points[i]
            
            if i == 0:
                p.slope_avg = None
                continue
            
            q = self.points[i-1]
            
            distance_d  = gpxpy.geo.distancePoints3D(p, q)
            elevation_d = p.elevation - q.elevation
            
            # skip stopped movements for computations
            # 10/06/2017 (remove high slopes on stops)
            # the average slope is not well computed.
            
            #if distance_d <1.0:
            #    p.slope_avg = None
            #    continue
            
            distance_incr += distance_d
            elevation_incr += elevation_d            
            
            ## print "[%5d] D: %7.2f | E: %7.2f" % (i, distance_incr, elevation_incr)
            
            if distance_incr >= self.distance_gap:
                # calculate average.
                # set before points ???
                p.slope_avg = gpxpy.geo.gradeslope(distance_incr,elevation_incr)
                print("* D: %7.2f | E: %7.2f | S: %3.2f" % (distance_incr, elevation_incr, p.slope_avg))
                distance_incr = 0.0
                elevation_incr = 0.0                
            else:
                p.slope_avg = None
        
        # manage trail ?
        p.slope_avg = gpxpy.geo.gradeslope(distance_incr,elevation_incr)        
        
        # fix the holes.
        i = 0
        while i < len(self.points):
            p = self.points[i]
            if p.slope_avg == None:
                for j in range(i+1, len(self.points)):
                    q = self.points[j]
                    if q.slope_avg != None:
                        for k in range(i,j):
                            r = self.points[k]
                            r.slope_avg = q.slope_avg
                            
                        i = j+1
                        break
            else:
                i += 1
            
                    
            
            
            
    
if __name__ == "__main__":
    
    slope = SlopeManager(10)
    slope.LoadGPX(sys.argv[1])
    
    slope.ComputeSlope()
    r = slope.DumpPoints()
    
    fd = open("dump.html","w+")
    fd.write(r)
    fd.close()
    
    
    

 
