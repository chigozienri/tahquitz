import copy,math,subprocess,re
from sklearn import linear_model
# apt-get install python-sklearn
# This is in python2 because sklearn seems to be python2.

# State as of 2019 jul 22:
#   Implemented two methods of finding the mapping from GPS coords to pixel coords. The first is a totally free linear
#   regression, which can be unphysical because the simulated camera's basis vectors can fail to be orthogonal. This method
#   also doesn't necessarily give well-determined results if the points all lie in the same plane, which mine basically do.
#   The second method is basically a four-parameter fit to the camera's altitude, azimuth, roll, and scale. As with the
#   first method, the projection is for a perspective at infinity. The pixel coordinates are also displaced in order
#   to match the average of the data; this confuses me -- shouldn't the alt-az stuff be sufficient for aiming?
#   When the number of points is small (is currently 2 for the high-numbered images), there is certainly not enough
#   data to determine this many parameters.
#   Currently I calculate method 1, then immediately overwrite it with method 2.
#   Results are OK, not great.
#   The code writes svg files err_NN.svg, which give a graphical depiction of the errors.
#   It seems to want to use big roll angles, even when the trees in the image are clearly not off vertical by more than a couple of degrees.
#   The data contains my estimated error bars on the camera locations, but currently doesn't do anything with these, and
#   we don't try to vary the camera location in order to improve the fit. Could do that, and also maybe try to model
#   aberration somehow, although I would probably need a ton more data for that.
#   The errors seem to be a continuous vector field, i.e., differential errors seem to be small for nearby points.
#   This means that I could probably, e.g., very accurately estimate GPS coords for a belay on one climb if I knew
#   GPS data for a climb next to it on the rock.
#   Distances range from 0.74 to 5.0 km, so angles can be as big as 75 degrees from center to corner of photo. Expect
#   huge aberrations for these nearby points of view. If aberrations cause angular errors as big as O(theta^2), then
#   they can be ginormous. It's conceivable that I could use data from hugin to correct for this completely, but I
#   didn't preserve the data, would need to redo the photos or reconstruct the projections. Some images, such as the
#   one from Pine Cove, are single frames rather than mosaics, but I have a paucity of data for them.
#   I have some points that seem useful because they are visible on almost every photo:
#     summit
#     jensens-jaunt-5 (top of boulder)
#     trough-2 (pine tree ledge)
#     tall-tree-below-lunch-ledge (off route a little to the right, in 4th class terrain)
#   It would be very helpful to get actual GPS coordinates for the remaining ones of these.
#   Notation:
#     (x,y,z) = UTM coordinates, NAD83, relative to corner of 1 km squarethat includes Tahquitz
#     (i,j) = pixel coordinates, origin at opper left
#     c = data structure containing 8 coefficients of the linear transformation from xyz to ij:
#       i = ax+by+cz+constant
#       j = similar

def find_image_file(filename):
  return "/home/bcrowell/Tahquitz_photography/mosaics/"+filename+".jpg"

def main():
  analyze()

def init():
  images = []
  dat = []

  # If adding a new image to this list, add its size to the cached list of sizes inside get_image_size(); otherwise
  # it will be horribly slow.
  im00 = image(images,"00","00_satellite",is_satellite=True)
  im01 = image(images,"01","01_northeast_from_saddle_jct",loc="530291 3737145 2469",loc_err=[1000,1000])
  im05 = image(images,"05","05_north_side_from_saddle_jct",loc="530300 3737500 2606",loc_err=[200,1000])
  im10 = image(images,"10","10_north_face_from_old_devils_slide_trail",loc="529854 3737073 2353",loc_err=[200,200])
  im15 = image(images,"15","15_panorama_from_low_on_devils_slide",loc="529129 3736244 1999",loc_err=[600,600])
  im20 = image(images,"20","20_northwest_face_from_deer_springs_slabs",loc="525884 3735229 1780",loc_err=[300,1000])
  im25 = image(images,"25","25_northwest_face_from_suicide_junction",loc="526901 3736497 2100",loc_err=[50,50])
  im30 = image(images,"30","30_from_fern_valley",loc="527612 3735142 1731",loc_err=[30,30])
  im35 = image(images,"35","35_tahquitz_rock_from_pine_cove_ca",loc="524485 3734651 1829",loc_err=[200,400])
  im40 = image(images,"40","40_west_side_from_auto_parts_store",loc="525931 3733312 1508",loc_err=[30,30])
  im50 = image(images,"50","50_south_face_from_bottom_of_maxwell_trail",loc="527668 3733230 1754",loc_err=[30,30])
  im90 = image(images,"90","90_satellite_esri_clarity",is_satellite=True)

  #--------- Points with absolute positions measured by GPS:

  p = point("uneventful-4",[366,662,2327],"left side of big J tree ledge")
  pix(dat,p,im01,1775,2130)
  pix(dat,p,im05,1967,1671)
  pix(dat,p,im10,2284,1675)

  p = point("summit",[347.0,623.0,2439.0],"summit")
  pix(dat,p,im00,3154,2320)
  # ...identified by shadow of summit block and in relation to overhangs on northeast and big crag to the west; may be wrong
  pix(dat,p,im01,2010,326)
  pix(dat,p,im05,2145,360)
  pix(dat,p,im10,2493,280)
  pix(dat,p,im15,5316,684) # can't actually see the point, slightly hidden, but very close to this position
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
  pix(dat,p,im15,6939,4052)

  p = point("west-lark-0",[388,797,2174],"base of rock; is the same location as the start of the other larks")
  pix(dat,p,im00,3654,1068)

  p = point("el-whampo-0",[510,782,2163],"foot of class 4/easy 5th gully that is the first easy pitch of El Whampo")
  pix(dat,p,im00,4690,1230) # x may be off

  #--------- Points without absolute positions measured by GPS:

  p = point("lunch-rock",None,"not certain this is actually Lunch Rock; point is black crevice near north side")
  pix(dat,p,im00,1566,2151)
  pix(dat,p,im90,1600,4941)

  p = point("square-flake-inside-lambda",None,"corner of distinctive square flake in the middle of the Northeast Face lambda")
  pix(dat,p,im00,4078,1497)
  pix(dat,p,im01,1028,3886)
  pix(dat,p,im05,1480,2893)
  pix(dat,p,im15,930,5166) # could be off by (-70,-70) pixels, but I think this is actually it
  pix(dat,p,im90,4151,4293)

  p = point("jensens-jaunt-5",None,"north/top tip of boulder at end of Jensen's Jaunt, final slab pitch; z from DEM")
  # Tried clicking in google maps to get lat-lon, then finding UTM from that, then elevation from DEM. Results were
  # 529163 3735553 2330. But this made results horrible, probably because google maps is using some different datum.
  pix(dat,p,im00,1978,2846)
  pix(dat,p,im05,3182,1310)
  pix(dat,p,im10,4092,1459)
  pix(dat,p,im15,9428,3364)
  pix(dat,p,im20,2650,1416)
  pix(dat,p,im25,1720,630)
  pix(dat,p,im30,1638,577)
  pix(dat,p,im35,2103,1351)
  pix(dat,p,im40,1443,964)
  pix(dat,p,im50,1170,1410)

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
  # Transformation from UTM to satellite pixels is done by code in subdirectory satellite:
  coeff['00'] = [
    [[8.38053607, -0.69082108, 0.0],962.506047077437],
    [[-0.02427133, -8.11101721, 0.0],7342.9289958528725]
  ]
  coeff['90'] = [
    [[8.088, 0.0, 0.0],629.8],
    [[0, -8.080, 0.0],10108.0]
  ]
  #------
  print "Coefficients of transformation from GPS to pixels:"
  for im in images:
    label = im[0]
    if not (label in coeff):
      continue
    print "  ",im[1] # filename
    c = coeff[label]
    print "    ",c[0]
    print "    ",c[1]
  #------------ 
  print "Lines of sight (camera to rock, azimuth defined ccw from E):"
  for im in images:
    label = im[0]
    print "  ",im[1] # filename
    if label in coeff:
      c = coeff[label]
      # If we express pixels coordinates i and j in terms of x, y, and z, then the gradients of the functions i and j give
      # vectors parallel to the pixel axes. Taking the cross product of these gives the direction of the line of sight.
      i_gradient = [c[0][0][0],c[0][0][1],c[0][0][2]]
      j_gradient = [c[1][0][0],c[1][0][1],c[1][0][2]]
      los = normalize(cross_product(i_gradient,j_gradient)) # oriented from camera to rock, since j points down
      alt,az = los_to_alt_az(los)
      print "    from fit,     azimuth=",deg(az),", alt=",deg(alt)
    if not (im[2] is None):
      loc = im[2]
      los,dist,alt,az,roll = expected_aar(loc)
      print "    from mapping, azimuth=",deg(az),", alt=",deg(alt),",   distance=",dist/1000.0," km"
  #------------ 
  print "Results of mapping from GPS to pixels, compared with actual pixel locations, from fit:"
  sum_sq = 0.0
  n = 0
  for im in images:
    label = im[0]
    print "  ",im[1] # filename
    if not (label in coeff):
      continue
    c = coeff[label]
    this_n,per_df,est_rescale,est_i_shift,est_j_shift = goodness_one_image(dat,im,c,if_print=True)
    if not (this_n is None):
      n = n+this_n
      sum_sq = sum_sq+per_df*this_n
  print "  n=",n,"  rms error=",math.sqrt(sum_sq/n)
  #------------ 
  print "Changing coefficients for ground-based images to what we expect from mapping, then optimizing orientation and scale:"
  for im in images:
    if is_satellite(im):
      continue
    label = im[0]
    loc = im[2]
    dim = im[4] # [w,h] of image, in pixels
    debug = False
    if loc is None:
      continue
    print "  ",im[1] # filename
    guess_scale = (5.0e4)*(dim[1]/6500.0)/dist # just a rough guess based on how many pixels I normally use to cover the rock vertically
    los,dist,alt,az,roll = expected_aar(loc)
    scale = guess_scale
    c = coeffs_from_altaz(loc,alt,az,roll,scale,dim)
    if debug:
      print "    initial estimates:"
      goodness_one_image(dat,im,coeffs_from_altaz(loc,alt,az,roll,scale,dim),if_print=True)

    this_n,per_df,est_rescale,est_i_shift,est_j_shift = goodness_one_image(dat,im,c,if_print=False)
    print "    estimated rescaling = ",est_rescale
    if this_n>=2:
      scale = scale*est_rescale

    n = count_observations(dat,im)
    if n<2:
      print "    can't optimize, number of observations is only ",n
      continue
    par_names = ["alt","az","roll","scale"]
    par = [alt,az,roll,scale]
    printing = [lambda x:deg(x),lambda x:deg(x),lambda x:deg(x),lambda x:("%5.3e" % x)]
    constr = lambda p : abs(p[2])<rad(20.0) and abs(p[0]-alt)<rad(20.0) and abs(p[1]-az)<rad(5.0)
    # ... limit changes in alt, az, and roll
    delta = [rad(1.0),rad(1.0),rad(1.0),scale*0.01]
    goodness = lambda p : goodness_one_image(dat,im,coeffs_from_altaz(loc,p[0],p[1],p[2],p[3],dim),if_print=False)[1]
    print "    initial guesses for parameters: ",altaz_pars_to_str(par,printing)
    par2 = par

    par2 = minimize(goodness,par2,delta,par_names,if_print=False,printing_funcs=printing,n_print=10,constraint=constr,allow=[True,True,True,True])
    if debug:
      print "    final:"
      goodness_one_image(dat,im,coeffs_from_altaz(loc,par2[0],par2[1],par2[2],par2[3],dim),if_print=True)

    alt,az,roll,scale = par2
    scale = scale
    c = coeffs_from_altaz(loc,alt,az,roll,scale,dim)
    coeff[label] = c
    print "    improved parameters:            ",altaz_pars_to_str(par2,printing)
    this_n,per_df,est_rescale,est_i_shift,est_j_shift = goodness_one_image(dat,im,c,if_print=True)
    if not (this_n is None) and this_n>0:
      if n==2:
        print "    exact fit, only 2 x-y points to determine 4 parameters"
      else:
        rms = math.sqrt(per_df*n/(n-2.0)) # root mean square error, in pixels
        pct = 100.0*rms/pythag2(dim[0],dim[1]) # as a percentage of image size
        print "    n=",this_n,"  rms error=",int(rms)," pixels =",("%4.1f" % pct)," % of image size ~",int(rms/scale)," m"
    ang_scale = angular_scale(loc,c) # radians per pixel
    print "    distance = ",("%4.1f" % (dist/1000.0))," km"
    print "    angular scale ~ ",("%.2e" % ang_scale)," pixels/radian = ",("%.2e" % deg_float(ang_scale))," pixels/degree"
    max_angle = 0.5*pythag2(dim[0],dim[1])*ang_scale
    print "    max angle ~",("%.2e" % max_angle)," radians = ",("%5.1f" % deg_float(max_angle))," deg"
    print "    max theta^2 ~ ",("%.2e" % (max_angle**2/ang_scale))," pixels ~ ",("%.2e" % (max_angle**2/(ang_scale*scale)))," m"

def minimize(f,x_orig,dx_orig,names,if_print=False,printing_funcs=None,n_print=1,constraint=None,allow=None):
  x = copy.copy(x_orig)
  dx = copy.copy(dx_orig)
  for iter in range(300):
    for i in range(len(x)):
      if not (allow is None) and not allow[i]:
        continue # not allowed to adjust this parameter
      improved,x2 = improve(f,x,dx,i,constraint)
      if improved:
        x=x2
        dx[i]=dx[i]*1.1
      else:
        dx[i]=dx[i]*0.75
    if if_print and iter%n_print==0:
      print altaz_pars_to_str(x,printing_funcs),dx,("%8.6e" % math.sqrt(f(x)))
  return x

def altaz_pars_to_str(x,printing_funcs):
  xp = []
  for i in range(len(x)):
    xp.append(printing_funcs[i](x[i]))
  return str(xp)

def improve(f,x,dx,i,constraint):
  f0 = f(x)
  # Try raising it:
  x2 = copy.copy(x)
  x2[i] = x2[i]+dx[i]
  f2 = f(x2)
  if f2<f0 and constraint(x2):
    return [True,x2]
  # Try lowering it:
  x2 = copy.copy(x)
  x2[i] = x2[i]-dx[i]
  f2 = f(x2)
  if f2<f0 and constraint(x2):
    return [True,x2]
  # No improvement:
  return [False,x]

def angular_scale(loc,c):
  # Approximate angular scale, in radians per pixel, based on heart of rock and summit.
  # This doesn't make sense for satellite view, both because I don't know how high the satellite is and because the two
  # points will almost exactly line up from overhead.
  # two lines of sight:
  p1 = heart_of_rock()
  p2 = summit_position()
  los1 = sub_vectors(p1,loc)
  los2 = sub_vectors(p2,loc)
  angle = math.acos(dot_product(normalize(los1),normalize(los2)))
  ij1 = gps_to_pixel(p1,c)
  ij2 = gps_to_pixel(p2,c)
  pixels = pythag2(ij1[0]-ij2[0],ij1[1]-ij2[1])
  if angle<0.01:
    return None # satellite view
  else:
    return angle/pixels

def coeffs_from_altaz(loc,alt,az,roll,scale,dim):
    # The constant terms are off by quite a bit. We correct them later as a side-effect of calling goodness_one_image(),
    # which does a first pass in order to adjust them.
    r = rotation_matrix(alt,az-math.pi/2.0,roll) # subtract 90 from az, because line of sight is z, to when az=0, x is south
    a = scalar_mult_matrix(r,scale)
    vs = -1.0 # pixel coordinates in the vertical direction are increasing downward
    ic = [a[0][0],a[1][0],a[2][0]] # camera's basis vector pointing to the right
    jc = [a[0][1],a[1][1],a[2][1]] # camera's basis vector pointing up
    los = sub_vectors(heart_of_rock(),loc) # line of sight
    i_const =    -dot_product(ic,los)+dim[0]/2.0
    j_const = -vs*dot_product(jc,los)+dim[1]/2.0
    c = [
      [                ic,i_const],
      [scalar_mult(jc,vs),j_const]
    ]
    return c

def pix(dat,p,im,i,j):
  # (i,j) = pixel coordinates with respect to top left (the convention used in gimp)
  dat.append([p,im,[float(i),float(j)]])

def image(list,label,filename,loc=None,loc_err=None,is_satellite=False):
  # The optional loc argument is the UTM coords of the camera, and loc_err=[x,y] is an estimate of the possible error in the horizontal coordinates.
  w,h = [get_image_size(filename,'w'),get_image_size(filename,'h')]
  im = [label,filename,utm_input_convenience(loc),loc_err,[w,h],is_satellite]
  list.append(im)
  return im

def is_satellite(im):
  return im[5]

def get_image_size(filename,dim):
  # dim can be 'w' or 'h'
  cached_sizes = {"00_satellite":[6688, 4624],
    "01_northeast_from_saddle_jct":[3077, 5357],
    "05_north_side_from_saddle_jct":[4512, 3664],
    "10_north_face_from_old_devils_slide_trail":[5280, 4720],
    "15_panorama_from_low_on_devils_slide":[11885, 6500],
    "20_northwest_face_from_deer_springs_slabs":[3264, 4896],
    "25_northwest_face_from_suicide_junction":[2720, 4592],
    "30_from_fern_valley":[2723, 2447],
    "35_tahquitz_rock_from_pine_cove_ca":[3096, 4096],
    "40_west_side_from_auto_parts_store":[3157, 2983],
    "50_south_face_from_bottom_of_maxwell_trail":[3586, 3554],
    "90_satellite_esri_clarity":[6758,7000]
    }
  if filename in cached_sizes:
    d = cached_sizes[filename]
    if dim=='w':
      return d[0]
    else:
      return d[1]
  print "********* warning, no size cached for image ",filename,", performance will be horrible"
  return int(subprocess.check_output('identify -format "%['+dim+']" '+find_image_file(filename),shell=True))


def point(name,coords,description):
  # Define a new point on the rock, such as a belay, but its UTM coordinates (NAD83).
  # Coordinates can be in any of the forms accepted by utm_input_convenience().
  coords = utm_input_convenience(coords)
  return {"name":name,"p":coords,"description":description}

def count_observations(dat,im):
  sum_sq = 0.0
  n = 0
  for obs in dat:
    p,im2,ij = obs
    if p["p"] is None or im2!=im:
      continue
    n = n+1
  return n

def goodness_one_image(dat,im,c,if_print):
  # Modifies c.
  this_n,per_df,est_rescale,est_i_shift,est_j_shift = goodness_one_image_one_pass(dat,im,c,False)
  if this_n==0:
    return [this_n,per_df,est_rescale,est_i_shift,est_j_shift]
  c[0][1] += est_i_shift
  c[1][1] += est_j_shift
  this_n,per_df,est_rescale,est_i_shift,est_j_shift = goodness_one_image_one_pass(dat,im,c,if_print)
  return [this_n,per_df,est_rescale,est_i_shift,est_j_shift]

def goodness_one_image_one_pass(dat,im,c,if_print):
  i_obs = []
  j_obs = []
  i_pred = []
  j_pred = []
  sum_sq = 0.0
  n = 0
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
    coords_pred = gps_to_pixel(gps,c)
    for coord in range(2):
      co_obs = ij[coord]
      obs.append(co_obs)
      co_pred = coords_pred[coord]
      pred.append(co_pred)
      err.append(co_pred-co_obs)
      sum_sq = sum_sq+(co_pred-co_obs)*(co_pred-co_obs)
    n = n+1
    i_obs.append(obs[0])
    j_obs.append(obs[1])
    i_pred.append(pred[0])
    j_pred.append(pred[1])
    if if_print:
      print "    obs=(%4d,%4d), pred=(%4d,%4d), err=(%4d,%4d) %s" % (obs[0],obs[1],pred[0],pred[1],err[0],err[1],descr)
  if n==0:
    return [None,None,1.0,0.0,0.0]
  if True:
    do_svg_error_arrows(im[0],im[4],find_image_file(im[1]),i_obs,j_obs,i_pred,j_pred)
  if n>=2:
    z = std_dev(i_pred)**2+std_dev(j_pred)**2
    est_rescale = math.sqrt((std_dev(i_obs)**2+std_dev(j_obs)**2)/z)
  else:
    est_rescale = 1.0
  est_i_shift = avg(i_obs)-avg(i_pred)
  est_j_shift = avg(j_obs)-avg(j_pred)
  return [n,sum_sq/n,est_rescale,est_i_shift,est_j_shift]

def gps_to_pixel(gps,c):
  ij = []
  for coord in range(2):
    co_pred = c[coord][1]
    for m in range(3):
      co_pred = co_pred + c[coord][0][m]*gps[m]
    ij.append(co_pred)
  return ij

def do_svg_error_arrows(label,dim,filename,i_obs,j_obs,i_pred,j_pred):
  svg_code = """
  <?xml version="1.0" encoding="UTF-8" standalone="no"?>
  <!-- Created with Inkscape (http://www.inkscape.org/) -->
  <svg   xmlns:svg="http://www.w3.org/2000/svg"   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"  xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs
     id="defs2">
    <marker
       inkscape:stockid="Arrow1Lend"
       orient="auto"
       refY="0.0"
       refX="0.0"
       id="Arrow1Lend"
       style="overflow:visible;"
       inkscape:isstock="true">
      <path
         id="path820"
         d="M 0.0,0.0 L 5.0,-5.0 L -12.5,0.0 L 5.0,5.0 L 0.0,0.0 z "
         style="fill-rule:evenodd;stroke:#d60000;stroke-width:1pt;stroke-opacity:1;fill:#d60000;fill-opacity:1"
         transform="scale(0.8) rotate(180) translate(12.5,0)" />
    </marker>
  </defs>
  RECTANGLE
  IMAGE
  ARROWS
  </svg>
  """.strip()
  arrow = """
    <path
       style="opacity:1;vector-effect:none;fill:none;fill-opacity:1;stroke:#dd0000;stroke-width:0.176;stroke-opacity:1;marker-end:url(#Arrow1Lend)"
       d="M _X,_Y l _DX,_DY" />
  """.strip()
  rect = """
  <rect
     style="fill:#dbdbdb;fill-opacity:1;stroke:none;stroke-width:0.6861555;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1"
     id="rect829"
     width="_WIDTH"
     height="_HEIGHT"
     x="0"
     y="0" />
  """.strip()
  image = """
    <image
     sodipodi:absref="_FILENAME"
     y="0"
     x="0" 
     id="image930"   
     xlink:href="_FILENAME"
     preserveAspectRatio="none"
     height="_HEIGHT"
     width="_WIDTH" />
  """.strip()
  arrows = ''
  s = 0.03
  for m in range(len(i_obs)):
    i = i_obs[m]
    j = j_obs[m]
    i_err = i_pred[m]-i_obs[m]
    j_err = j_pred[m]-j_obs[m]
    a = copy.copy(arrow)
    a = re.sub("_X",str(i*s),a)
    a = re.sub("_Y",str(j*s),a)
    a = re.sub("_DX",str((i_err)*s),a)
    a = re.sub("_DY",str((j_err)*s),a)
    arrows = arrows + a + "\n    "
  w = str(dim[0]*s)
  h = str(dim[1]*s)
  rect = re.sub("_WIDTH",w,rect)
  rect = re.sub("_HEIGHT",h,rect)
  image = re.sub("_FILENAME",filename,image)
  image = re.sub("_WIDTH",w,image)
  image = re.sub("_HEIGHT",h,image)
  svg_code = re.sub("RECTANGLE",rect,svg_code)
  svg_code = re.sub("IMAGE",image,svg_code)
  svg_code = re.sub("ARROWS",arrows,svg_code)
  with open("err_"+label+".svg", 'w') as f:
    f.write(svg_code+"\n")

def avg(x):
  n = len(x)
  av = 0.0
  for i in range(len(x)):
    av = av+x[i]
  return av/n

def std_dev(x):
  n = len(x)
  av = avg(x)
  sd = 0.0
  for i in range(len(x)):
    sd = sd+(x[i]-av)**2
  return math.sqrt(sd/n)

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
  #   "530300 3737500" ... estimate z from DEM
  #   "111 222 2606" ... NAD83 coords in meters, relative to the UTM square containing the rock
  #   [111,222 2606]
  # If input is None, returns None.
  if p is None:
    return None
  if isinstance(p,str):
    return utm_input_convenience(map(lambda x:float(x),p.split()))
  x,y,z = p
  if x>1000.0 or y>1000.0 or x<0.0 or y<0.0:
    x = x-reference_point()[0]
    y = y-reference_point()[1]
  if pythag2(x,y)>1.0e5:
    raise RuntimeError('Distance from reference point fails sanity check.');
  return [float(x),float(y),float(z)]

def rotation_matrix(altitude,azimuth,roll):
  # active rotations that you would apply to the camera
  rx = rotation_matrix_one_axis(0,-roll) # roll>0 means rotating the camera ccw
  ry = rotation_matrix_one_axis(1,-altitude)
  rz = rotation_matrix_one_axis(2,azimuth)
  return matrix_mult(rz,matrix_mult(ry,rx))

def rotation_matrix_one_axis(axis,angle):
  # axis=0, 1, 2 for x, y, z
  # angle in radians
  # Order of indices is such that applying the matrix to a vector is sum of a_{ij}x_j.
  a = zero_matrix()
  c = math.cos(angle)
  s = math.sin(angle)
  # The following is written with the axis=2 case in mind, in which case the rotation is in the xy plane, and cyc() is a no-op.
  a[cyc(2,axis+1)][cyc(2,axis+1)] = 1.0
  a[cyc(0,axis+1)][cyc(0,axis+1)] = c
  a[cyc(1,axis+1)][cyc(1,axis+1)] = c
  a[cyc(1,axis+1)][cyc(0,axis+1)] = s
  a[cyc(0,axis+1)][cyc(1,axis+1)] = -s
  return a

def matrix_mult(a,b):
  c = zero_matrix()
  for i in range(3):
    for j in range(3):
      for k in range(3):
        c[i][j] += a[i][k]*b[k][j]
  return c

def zero_matrix():
  return [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]

def cyc(n,k):
  return (n+k)%3

def add_vectors(u,v):
  return [u[0]+v[0],u[1]+v[1],u[2]+v[2]]

def sub_vectors(u,v):
  return [u[0]-v[0],u[1]-v[1],u[2]-v[2]]

def dot_product(u,v):
  return u[0]*v[0]+u[1]*v[1]+u[2]*v[2]

def norm(u):
  return math.sqrt(dot_product(u,u))

def scalar_mult(u,s):
  return [u[0]*s,u[1]*s,u[2]*s]

def scalar_mult_matrix(m,s):
  n = zero_matrix()
  for i in range(3):
    for j in range(3):
      n[i][j] = m[i][j]*s
  return n

def normalize(u):
  return scalar_mult(u,1.0/norm(u))

def pythag2(x,y):
  return math.sqrt(x*x+y*y)

def deg(x):
  return "%5.1f" % (x*180.0/math.pi)

def deg_float(x):
  return x*180.0/math.pi

def rad(x):
  return x*math.pi/180.0

def vec_to_str(u):
  return "[%5.4f,%5.4f,%5.4f]" % (u[0],u[1],u[2])

def expected_aar(loc):
  # expected line of sight, altitude, azimuth, and roll for a given camera location
  # azimuth is ccw from E
  displ = sub_vectors(heart_of_rock(),loc) # displacement to center of rock
  los = normalize(displ) # approximate line of sight
  distance = norm(displ)
  altitude,azimuth = los_to_alt_az(los)
  roll = 0.0
  return [los,distance,altitude,azimuth,roll]

def los_to_alt_az(los):
  # convert a line of sight to an altitude and azimuth
  altitude = math.atan2(los[2],pythag2(los[0],los[1]))
  if abs(los[0])<1.0e-5 and abs(los[1])<1.0e-5:
    azimuth = 0.0 # really undefined
  else:
    azimuth = angle_in_2pi(math.atan2(los[1],los[0]))
  return [altitude,azimuth]  

def reference_point():
  return [529000.0,3735000.0] # lower left corner of the UTM square containing the rock, (529 km,3735 km) in zone 11S.

def summit_position():
  return [347.0,623.0,2439.0] # see comments in util_gps.rb

def heart_of_rock():
  p = summit_position()
  p[2] = p[2]-100.0 # an approximation to where we're pointing the camera
  return p
  
main()
