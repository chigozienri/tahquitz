import copy,math
from sklearn import linear_model
# apt-get install python-sklearn
# This is in python2 because sklearn seems to be python2.

def main():
  analyze()

def init():
  images = []
  dat = []

  im01 = image(images,"01","01_northeast_from_saddle_jct")
  im05 = image(images,"05","05_north_side_from_saddle_jct",loc="530300 3737500 2606",loc_err=[200,2000])
  im10 = image(images,"10","10_north_face_from_old_devils_slide_trail",loc="529854 3737073 2353",loc_err=[200,200])
  im15 = image(images,"15","15_panorama_from_low_on_devils_slide",loc="529129 3736244 1999",loc_err=[600,600])
  im20 = image(images,"20","20_northwest_face_from_deer_springs_slabs",loc="525884 3735229 1780",loc_err=[300,1000])
  im25 = image(images,"25","25_northwest_face_from_suicide_junction",loc="26901 36497 2100",loc_err=[50,50])
  im30 = image(images,"30","30_from_fern_valley",loc="527612 3735142 1731",loc_err=[30,30])
  im35 = image(images,"35","35_tahquitz_rock_from_pine_cove_ca",loc="524485 3734651 1829",loc_err=[200,400])
  im40 = image(images,"40","40_west_side_from_auto_parts_store",loc="525931 3733312 1508",loc_err=[30,30])
  im50 = image(images,"50","50_south_face_from_bottom_of_maxwell_trail",loc="527668 3733230 1754",loc_err=[30,30])

  #--------- Points with absolute positions measured by GPS:

  p = point("uneventful-4",[366,662,2327],"left side of big J tree ledge")
  pix(dat,p,im01,1775,2130)
  pix(dat,p,im05,1967,1671)
  pix(dat,p,im10,2284,1675)

  p = point("summit",[347.0,623.0,2439.0],"summit")
  pix(dat,p,im01,2010,326)
  pix(dat,p,im05,2145,360)
  pix(dat,p,im10,2493,280)
  pix(dat,p,im20,1575,317) # not totally sure of identification
  pix(dat,p,im35,1562,531) # approximate location, view obscured by rock in front?
  pix(dat,p,im40,1930,140)
  pix(dat,p,im50,2451,599)

  p = point("error-2",[327,730,2240],"ledge under overhangs; left-right position uncertain by a few meters")
  pix(dat,p,im01,2791,3923)
  pix(dat,p,im05,2560,2925)
  pix(dat,p,im10,3128,3072)
  pix(dat,p,im15,4322,4786)

  p = point("error-3",[328,715,2270],"middle (?) of rubble-strewn ledge")
  pix(dat,p,im01,2542,3434)
  pix(dat,p,im05,2442,2580)
  pix(dat,p,im10,2933,2701)
  pix(dat,p,im15,4232,4211)

  p = point("error-4",[336,694,2295],"alcove before steep part; poor agreement between photo surveying and GPS")
  pix(dat,p,im01,2329,3024)
  pix(dat,p,im05,2319,2301)
  pix(dat,p,im10,2755,2380)
  pix(dat,p,im15,4195,3818)

  p = point("north-buttress-1",[341,750,2230],"upper pine tree")
  pix(dat,p,im01,2637,4318)
  pix(dat,p,im05,2533,3198)
  pix(dat,p,im15,3368,5057)

  p = point("west-lark-0",[388,797,2174],"base of rock; is the same location as the start of the other larks")
  pix(dat,p,im01,2065,5280)

  p = point("maiden-0",[250,700,2248],"tree root on class 3 ledge, before the hard mantling move")
  pix(dat,p,im05,3131,2841)
  pix(dat,p,im10,4021,3010)

  p = point("maiden-1",[245,698,2277],"mountain mahogany (could be wrong)")
  pix(dat,p,im05,3109,2476)
  pix(dat,p,im10,3965,2604)
  pix(dat,p,im15,6839,4171)

  #--------- Points without absolute positions measured by GPS:

  p = point("trough-2",None,"pine tree ledge")
  pix(dat,p,im05,3131,1758)
  pix(dat,p,im10,4034,1919)
  pix(dat,p,im15,8774,3910)
  pix(dat,p,im20,1926,2113)
  pix(dat,p,im25,519,1417)
  pix(dat,p,im30,1106,1194)
  pix(dat,p,im35,1666,1839)

  p = point("tall-tree-below-lunch-ledge",None,"tall q-tip pine tree on ledges above optional belay and below lunch ledge, to right of 4th class on Angel's Fright")
  pix(dat,p,im05,3406,1793)
  pix(dat,p,im10,4464,1989)
  pix(dat,p,im15,10125,4218)
  pix(dat,p,im20,2253,2130)
  pix(dat,p,im25,1342,1572)
  pix(dat,p,im30,1236,1138)
  pix(dat,p,im35,1833,1873)
  pix(dat,p,im40,1016,1568)
  pix(dat,p,im50,688,2053)

  p = point("jensens-jaunt-5",None,"north, top tip of boulder at end of Jensen's Jaunt, final slab pitch")
  pix(dat,p,im05,3182,1310)
  pix(dat,p,im10,4092,1459)
  pix(dat,p,im15,9428,3364)
  pix(dat,p,im20,2650,1416)
  pix(dat,p,im25,1720,630)
  pix(dat,p,im30,1638,577)
  pix(dat,p,im35,2103,1351)
  pix(dat,p,im40,1443,964)
  pix(dat,p,im50,1170,1410)

  #--------- 

  return [images,dat]

def analyze():
  images,dat = init()
  coeff = {}
  for im in images:
    label = im[0]
    #print im[1] # filename
    c = [] # coefficients for this image
    mapping_determined = False
    for coord in range(2): # 0=i=horizontal coord of pixel in image, 1=j=vertical (from top)
      #print "  coord=",coord
      # In the following, x refers to the GPS coordinates and y to the pixel coordinates.
      x_list = []
      y_list = []
      for obs in dat:
        p,im2,ij = obs
        if im2!=im:
          continue
        y = ij[coord]
        if p["p"] is None:
          continue
        x = p["p"]
        descr = p["description"]
        print "    x=",x,"  y=",y,"   ",descr
        x_list.append(x)
        y_list.append(y)
      if len(x_list)<4:
        continue # not enough gps fixes for this point
      else:
        mapping_determined = True
      #print "  x_list=",x_list
      #print "  y_list=",y_list
      # https://stackoverflow.com/a/11479279/1142217
      clf = linear_model.LinearRegression(fit_intercept=True)
      clf.fit(x_list,y_list)
      #print "    ",clf.coef_," ",clf.intercept_
      c.append([copy.copy(clf.coef_),copy.copy(clf.intercept_)])
    if mapping_determined:
      coeff[label] = c
  sum_sq = 0.0
  n = 0
  #------------ Try to determine azimuths of images. This doesn't seem particularly accurate.
  print "Approximate azimuths based on modeling image planes (not very accurate):"
  for im in images:
    label = im[0]
    print "  ",im[1] # filename
    if not (label in coeff):
      continue
    c = coeff[label]
    # If we express pixels coordinates i and j in terms of x, y, and z, then the gradients of the functions i and j give
    # vectors parallel to the pixel axes. Taking the cross product of these gives the direction of the line of sight.
    i_gradient = [c[0][0][0],c[0][0][1],c[0][0][2]]
    j_gradient = [c[1][0][0],c[1][0][1],c[1][0][2]]
    los = cross_product(i_gradient,j_gradient) # oriented from camera to rock, since j points down
    az = angle_in_2pi(math.atan2(los[1],los[0])) # ccw from E
    print "    line of sight = ",los,", azimuth=",az*180.0/3.141," deg (ccw from E, camera to rock)"
  #------------ 
  print "Results of mapping from GPS to pixels, compared with actual pixel locations:"
  for im in images:
    label = im[0]
    print "  ",im[1] # filename
    if not (label in coeff):
      continue
    c = coeff[label]
    for obs in dat:
      p,im2,ij = obs
      if p["p"] is None:
        continue
      gps = p["p"]
      descr = p["name"]+", "+p["description"]
      if im2!=im:
        continue
      obs = []
      pred = []
      err = []
      for coord in range(2):
        co_obs = ij[coord]
        co_pred = c[coord][1]
        for m in range(3):
          co_pred = co_pred + c[coord][0][m]*gps[m]
        obs.append(co_obs)
        pred.append(co_pred)
        err.append(co_pred-co_obs)
        n = n+1
        sum_sq = sum_sq+(co_pred-co_obs)*(co_pred-co_obs)
      print "    obs=(%4d,%4d), pred=(%4d,%4d), err=(%4d,%4d) %s" % (obs[0],obs[1],pred[0],pred[1],err[0],err[1],descr)
  print "  n=",n,"  rms error=",math.sqrt(sum_sq/n)

def pix(dat,p,im,i,j):
  # (i,j) = pixel coordinates with respect to top left (the convention used in gimp)
  dat.append([p,im,[float(i),float(j)]])

def image(list,label,filename,loc=None,loc_err=None):
  # The optional loc argument is the UTM coords of the camera, and loc_err=[x,y] is an estimate of the possible error in the horizontal coordinates.
  im = [label,filename,loc,loc_err]
  list.append(im)
  return im

def point(name,coords,description):
  # Define a new point on the rock, such as a belay, but its UTM coordinates (NAD83).
  # Coordinates can be in any of the forms accepted by utm_input_convenience().
  coords = utm_input_convenience(coords)
  return {"name":name,"p":coords,"description":description}

def cross_product(u,v):
  x = u[1]*v[2]-u[2]*v[1]
  y = u[2]*v[0]-u[0]*v[2]
  z = u[0]*v[1]-u[1]*v[0]
  return [x,y,z]

def angle_in_2pi(x):
  if x<0.0:
    return x+2.0*math.pi
  else:
   return x

def utm_input_convenience(p):
  # Return coordinates in meters, NAD83, relative to reference point.
  # In this simplest case, where p is an array relative to ref point, returns p unchanged.
  # examples of what p can be:
  #   "530300 3737500 2606" ... NAD83 coords in meters
  #   "111 222 2606" ... NAD83 coords in meters, relative to the UTM square containing the rock
  #   [111,222 2606]
  # If input is None, returns None.
  if p is None:
    return None
  if isinstance(p,str):
    return utm_input_convenience(p.split())
  x,y,z = p
  if x>1000.0:
    x = x-reference_point()[0]
    x = x-reference_point()[1]
  return [float(x),float(y),float(z)]

def reference_point():
  return [529000.0,3735000.0] # lower left corner of the UTM square containing the rock, (529 km,3735 km) in zone 11S.
  

main()
