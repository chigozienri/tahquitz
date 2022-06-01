import copy,math,subprocess,re
from geom import *
from perspective import *

# Notes 2022 Jun 1:
#   Added photos 17 and 19. For 17, I did a shot with a plumb bob, so I know the image has almost zero roll. Although the
#   wind was blowing a little, so that the plumb bob wouldn't quite stop swinging, there's no way I'm off by more than
#   about a degree. And yet the arrow plot shows a rotation of about 5 degrees is needed -- why??? Seems like this has
#   to be a bug. I also noted below that trees are never off vertical by as much as the software would seem to require.
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
#     trough-2 (pine tree ledge)
#     tall-tree-below-lunch-ledge (off route a little to the right, in 4th class terrain)
#   It would be very helpful to get directly measured GPS coordinates, including z, for the remaining ones of these.
#   Notation:
#     (x,y,z) = UTM coordinates, NAD83, relative to corner of 1 km squarethat includes Tahquitz
#     (u,v,w) = coordinates in the camera's basis frame, defined so that the center of the image is at (0,0,w)
#     (i,j) = pixel coordinates, origin at upper left
#     c = data structure containing 8 coefficients of the linear transformation from xyz to ij:
#       i = ax+by+cz+constant
#       j = similar
#     roll = + means camera tilted cw, so trees in image tilt ccw
#  Notes on aberration/projection:
#    On most images, I can see that the trees in the bottom left and bottom right corners form lines that either converge or diverge in the upward direction.
#    This seems to be a relatively minor effect; if it was major, then I would see errors that would depend strongly on r, but I don't.
#    This is an indication of a common form of aberration/perspective distortion in photos. Expect the correction to be of the form
#      r -> Ar+Br^3
#    where r is distance from some point (i0,j0) which is the center of aberration. The A term is really just a rescaling by 1+A, but if scale has
#    already been adjusted globally, then introducing a nonzero B will require readjusting A as well. This is 4 d.f.: i0,j0,A,B.
#    The converging trees do not depend on A at all. If I assume that (i0,j0) is at the center of the image (why would it not be?), then
#    can basically choose B to parallelize the trees, then readjust scale. Or could simply use my existing fitting routines to fit B as
#    an additional parameter. On my error maps err_NN.svg, I'm seeing a combination of A and B, so can't just look at the error arrows and
#    interpret them as a measure of B, and they don't necessarily converge at the center of aberration.
#  Notes on using UTM as an approximation to Cartesian coordinates:
#    I verified by converting to Cartesian using proj4 library that UTM coordinates are orthogonal and isotropic to extremely good precision.
#    The angle between x-hat and y-hat rounds to 90 degrees to within machine precision. Isotropy is good to |xhat|/|yhat|-1 < 3e-9.
#    There is a scaling factor of approximately 0.9996 (see WP), but including that would not improve my results, would just introduce
#    inconveniences.

def find_image_file(filename):
  return "/home/bcrowell/Tahquitz_photography/mosaics/"+filename+".jpg"

def main():
  analyze()

def init():
  images = []
  dat = []

  # If adding a new image to this list, add its size to the cached list of sizes inside get_image_size(); otherwise
  # it will be horribly slow.

  im01 = image(images,"01","01_northeast_from_saddle_jct",loc="530291 3737145 2469",loc_err=[1000,1000],fudge_altaz=[14,0])
  im05 = image(images,"05","05_north_side_from_saddle_jct",loc="530300 3737500 2606",loc_err=[200,1000],fudge_altaz=[12,0])
  im10 = image(images,"10","10_north_face_from_old_devils_slide_trail",loc="529854 3737073 2353",loc_err=[200,200])
  im15 = image(images,"15","15_panorama_from_low_on_devils_slide",loc="529121 3736249 2002",loc_err=[10,10],fudge_altaz=[-20,10])
  # ... projection is rather bad on west lark, good on rest of image; can improve the fit on west lark by raising the elevation by 100 m,
  #     but then the rest of the fit gets worse
  im17 = image(images,"17","17_north_and_northwest_sides_from_strawberry_cienega",loc="528609 3738047 2608")
  im19 = image(images,"19","19_northwest_side_from_deer_springs_boulder_pile",loc="527054 3736907 2237")
  im20 = image(images,"20","20_northwest_face_from_deer_springs_slabs",loc="525884 3735229 1780",loc_err=[300,1000],tree_roll=7.5,fudge_altaz=[-10,0])
  im25 = image(images,"25","25_northwest_face_from_suicide_junction",loc="526901 3736497 2100",loc_err=[50,50],tree_roll=-1.0)
  im30 = image(images,"30","30_from_fern_valley",loc="527612 3735142 1731",loc_err=[30,30],fudge_altaz=[-15,0])
  im35 = image(images,"35","35_tahquitz_rock_from_pine_cove_ca",loc="524485 3734651 1829",loc_err=[200,400],tree_roll=7.8,fudge_altaz=[-10,0])
  im40 = image(images,"40","40_west_side_from_auto_parts_store",loc="525931 3733312 1508",loc_err=[30,30],tree_roll=0.5,fudge_altaz=[-10,0])
  im50 = image(images,"50","50_south_face_from_bottom_of_maxwell_trail",loc="527668 3733230 1754",loc_err=[30,30],tree_roll=1.0,fudge_altaz=[-12,0]) 
  # ... tree roll could be 0 to 2


  #--------- Points with absolute positions measured by GPS:

  p = point("trough-0",[187,634,2255],"start of The Trough")
  pix(dat,p,im10,4447,2812)
  pix(dat,p,im15,9170,5278)
  
  p = point("trough-2",[203,601,2320],"pine tree ledge") # average of two GPS fixes on same day; +-7 m on elevation
  pix(dat,p,im05,3131,1758)
  pix(dat,p,im10,4034,1919)
  pix(dat,p,im15,8774,3910)
  pix(dat,p,im17,6459,2204)
  pix(dat,p,im20,1926,2113)
  pix(dat,p,im25,519,1417)
  pix(dat,p,im30,1106,1194)
  pix(dat,p,im35,1666,1839)

  p = point("trough-3",[204,568,2358],"big pine tree at the top of the trough") 
  # ... x and z are average of [202,568,2360], [206,585,2356] from two different days; not sure I believe y of 2nd fix
  pix(dat,p,im05,3056,1274)
  pix(dat,p,im10,3898,1392)
  pix(dat,p,im15,8944,3228)
  pix(dat,p,im17,6567,1601)
  pix(dat,p,im20,2442,1384)
  pix(dat,p,im25,1249,494)
  pix(dat,p,im30,1548,611)
  pix(dat,p,im35,1996,1312)
  pix(dat,p,im40,1480,931)

  p = point("left-ski-track-0",[193,515,2282],"start of Left Ski Track, belaying at pine tree")
  pix(dat,p,im40,2034,2057)
  pix(dat,p,im50,1626,2565)

  p = point("left-ski-track-2",[200,545,2321],"big ledge at bottom of arete")
  pix(dat,p,im40,1834,1342)
  pix(dat,p,im50,1552,1832)

  p = point("left-ski-track-3",[185,553,2356],"tree at top")
  pix(dat,p,im40,1582,1022)
  pix(dat,p,im50,1323,1460)

  p = point("uneventful-4",[366,662,2327],"left side of big J tree ledge")
  pix(dat,p,im01,1775,2130)
  pix(dat,p,im05,1967,1671)
  pix(dat,p,im10,2284,1675)
  pix(dat,p,im17,3784,1834)

  p = point("summit",[347.0,623.0,2439.0],"summit")
  pix(dat,p,im01,2010,326)
  pix(dat,p,im05,2145,360)
  pix(dat,p,im10,2493,280)
  pix(dat,p,im15,5316,684) # can't actually see the point, slightly hidden, but very close to this position
  pix(dat,p,im17,4526,401)
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

  p = point("error-4",[336,694,2295],"alcove before steep part")
  pix(dat,p,im01,2329,3024)
  pix(dat,p,im05,2319,2301)
  pix(dat,p,im10,2755,2380)
  pix(dat,p,im15,4195,3818)

  p = point("north-buttress-1",[341,750,2230],"upper pine tree")
  pix(dat,p,im01,2637,4318)
  pix(dat,p,im05,2533,3198)
  pix(dat,p,im15,3368,5057)

  p = point("west-lark-0",[382,785,2188],"base of rock; is the same location as the start of the other larks; ad hoc combination of my fix from hike with dogs and Bethany's from belaying")
  pix(dat,p,im01,2065,5280)

  p = point("maiden-0",[250,700,2248],"tree root on class 3 ledge, before the hard mantling move")
  pix(dat,p,im05,3131,2841)
  pix(dat,p,im10,4021,3010)

  p = point("maiden-1",[252,708,2272],"mountain mahogany")
  # ... average of two measurements, [245,698,2277] and [258,718,2268]
  pix(dat,p,im05,3109,2476)
  pix(dat,p,im10,3965,2604)
  pix(dat,p,im15,6939,4052)

  #p = point("maiden-3",[271,662,2310],"large prostrate oak tree on left side of ledge")
  #pix(dat,p,im05,2882,1806)
  #pix(dat,p,im10,3586,1822)
  #pix(dat,p,im15,6624,2891)

  p = point("maiden-4opt",[289,654,2358],"optional belay at ledge with mountain mahogany, 10 meters below the standard belay")
  pix(dat,p,im05,2708,1370)
  pix(dat,p,im10,3311,1323)
  pix(dat,p,im15,6206,2090)

  p = point("maiden-6",[269,634,2399],"mahogany at end of slabs")
  pix(dat,p,im10,3349,834)
  pix(dat,p,im15,6701,1396)
  pix(dat,p,im17,5370,1030)

  p = point("west-lark-1",[382,760,2217],"first belay ledge; ID on photos very uncertain")
  pix(dat,p,im01,1957,4833)
  pix(dat,p,im05,2092,3536)

  p = point("west-lark-2",[382,735,2251],"middle/left of a set of 4-5 ledges; ID on photos very uncertain")
  pix(dat,p,im01,1818,4120)
  pix(dat,p,im05,1996,3055)
  pix(dat,p,im15,2226,5172)

  p = point("west-lark-3",[388,714,2279],"1 m above the gap in the overlaps; ad hoc combo of the z that I believe from my GPS and the x,y that I believe from Bethany's")
  pix(dat,p,im01,1648,3544)
  pix(dat,p,im05,1880,2669)
  pix(dat,p,im10,2168,2796)
  pix(dat,p,im15,2445,4551)

  p = point("west-lark-4",[391,685,2305],"half-way up the dihedral; can't really tell exact spot in photos")
  pix(dat,p,im01,1383,2819)
  pix(dat,p,im05,1703,2157)
  pix(dat,p,im10,1955,2219)
  pix(dat,p,im15,2625,3802)

  p = point("west-lark-5",[404,645,2335],"big belay ledge behind the table-sized flake; ID on photos somewhat uncertain")
  pix(dat,p,im01,1019,2017)
  pix(dat,p,im05,1460,1593)
  pix(dat,p,im10,1656,1595)
  pix(dat,p,im15,2721,3234)

  p = point("dead-tree-at-top-of-gendarme",[420,623,2378],"at end of larks, the dead tree that's visually prominent from below; extremely precise location of branch in 01, 05, and 10; GPS hanging from branch on climber's left; tree is about 10 m to the left of the final belay inside the gully; ")
  pix(dat,p,im01,515,1232)
  pix(dat,p,im05,1132,1043)
  pix(dat,p,im10,1255,1016)
  pix(dat,p,im15,2570,2250)
  pix(dat,p,im17,3218,1145)

  p = point("el-whampo-1",[488,715,2235],"on top of huge boulder, south of pine tree and at same height as middle of the tree")
  pix(dat,p,im05,753,3118)
  pix(dat,p,im17,1886,3510)

  p = point("northeast-rib-2",[496,685,2263],"small ledge with pine tree, to the right of the right-facing diheadral")
  pix(dat,p,im05,567,2684)

  p = point("northeast-rib-3",[487,687,2318],"sloping ledge on bottom right of orange rock, just above small pine tree, at end of right-facing dihedral")
  pix(dat,p,im05,599,2088)

  p = point("northeast-rib-4",[503,654,2319],"huge tree growing in niche above north gully, above the wooded area on NE rib and at same elevation as bottom of slabs in north gully")
  pix(dat,p,im05,491,1901) # inside tree, position uncertain by 20 pixels

  p = point("jensens-jaunt-5",[182,559,2349],"north/top tip of boulder at end of Jensen's Jaunt, final slab pitch")
  # ... raw datum was [182,556,2349], estimated to  be 3 m south of north tip
  pix(dat,p,im05,3182,1310)
  pix(dat,p,im10,4092,1459)
  pix(dat,p,im15,9428,3364)
  pix(dat,p,im20,2650,1416)
  pix(dat,p,im25,1720,630)
  pix(dat,p,im30,1638,577)
  pix(dat,p,im35,2103,1351)
  pix(dat,p,im40,1443,964)
  pix(dat,p,im50,1170,1410)

  p = point("fingertip-traverse-0",[110,531,2216],"on trail, at crack with succulents growing in it")
  pix(dat,p,im20,3144,3531) # can't see exact spot, could be off by 50 pixels
  pix(dat,p,im30,1738,2111) # can't see exact spot, could be off by 50 pixels
  pix(dat,p,im35,2376,2834) # can't see exact spot, could be off by 50 pixels
  pix(dat,p,im40,1057,2664) # decent view, only slightly obscured
  # Didn't get GPS fix for ant tree, belay 1.
  p = point("fingertip-traverse-2",[121,553,2261],"jungle ledge, on fingertip traverse, highest of the three small oak trees")
  # ... Original fix was [121,553,2276]. This z has to be wrong, can't just be 13 m below belay 3. Dropped it by 15 m to fit photo.
  pix(dat,p,im20,2750,2880)
  pix(dat,p,im25,2185,2709)
  pix(dat,p,im30,1503,1639)
  pix(dat,p,im35,2129,2393)
  pix(dat,p,im40,1043,2151)
  pix(dat,p,im50,470,2677)
  p = point("fingertip-traverse-3",[142,561,2289],"small ledge before the traverse; intersection of two cracks in a Y")
  pix(dat,p,im30,1445,1355)
  pix(dat,p,im35,2041,2115)
  pix(dat,p,im40,1070,1836)
  pix(dat,p,im25,1930,2133)
  pix(dat,p,im20,2601,2480)
  p = point("fingertip-traverse-4",[166,578,2315],"lunch ledge")
  pix(dat,p,im15,10107,4101) # view obscured by q-tip tree, could be off by 30 pixels
  pix(dat,p,im20,2322,2055)
  pix(dat,p,im25,1400,1440)
  pix(dat,p,im30,1277,1055)
  pix(dat,p,im35,1870,1800)
  pix(dat,p,im40,1054,1508) # poor view, could be off by 20 pixels
  p = point("fingertip-traverse-5",[174,569,2330],"flakes above oak trees, where the route forks into three variations")
  pix(dat,p,im15,10007,3859)
  pix(dat,p,im20,2468,1757)
  pix(dat,p,im25,1568,1104)
  pix(dat,p,im30,1426,846)
  pix(dat,p,im35,1959,1622)
  pix(dat,p,im40,1196,1268)
  pix(dat,p,im50,865,1763)
  p = point("fingertip-traverse-6",[199,568,2360],"oak tree above lunch ledge slabs, just a few feet to the right of end of the trough")
  # GPS data point was clearly an error, was a dupe of jensens-jaunt-5. These coords are simply trough-3 plus a westward displacement of 3 m.
  pix(dat,p,im15,9102,3280)
  pix(dat,p,im20,2477,1392)
  pix(dat,p,im25,1345,541)
  pix(dat,p,im30,1544,614)
  pix(dat,p,im35,2025,1336)
  pix(dat,p,im40,1433,958)

  p = point("lunch-rock",[112,629,2224],"top/center of lunch rock")
  pix(dat,p,im17,7645,3798)
  pix(dat,p,im35,1114,3086)

  #--------- Points without absolute positions measured by GPS:

  #p = point("west-lark-3",[370,729,2279],"1 m above the gap in the overlaps; ID on photos somewhat uncertain")
  # ... GPS coordinates off by about 10 meters to the west; route is actually straight and trends to the east
  p = point("west-lark-3",None,"1 m above the gap in the overlaps; ID on photos somewhat uncertain")
  pix(dat,p,im01,1605,3425)
  pix(dat,p,im05,1850,2587)
  pix(dat,p,im10,2130,2683)
  pix(dat,p,im15,2449,4431)

  p = point("friction-descent-boulder",[249,590,2386],"top of split, house-size boulder at top of friction descent, surrounded by brush")
  pix(dat,p,im35,1818,1014) # desired point slightly obscured, guessing at exact height
  pix(dat,p,im40,1625,617)
  pix(dat,p,im50,1724,1072)

  p = point("lunch-rock-clearing",None,"second large open space west of lunch rock; likely accurate DEM because of flat ground")
  pix(dat,p,im35,1699,3883)

  p = point("square-flake-inside-lambda",None,"corner of distinctive square flake in the middle of the Northeast Face lambda")
  pix(dat,p,im01,1028,3886)
  pix(dat,p,im05,1480,2893)
  pix(dat,p,im15,930,5166) # could be off by (-70,-70) pixels, but I think this is actually it

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
  #------------
  pr = {} # hash of perspectives by label of image 
  print "Determining perspective mappings:"
  for im in images:
    n = count_observations(dat,im)
    if n<2:
      continue
    label = im[0]
    loc = im[2]
    dim = im[4] # [w,h] of image, in pixels
    debug = False
    if loc is None:
      continue
    print "  ",im[1] # filename
    los,dist,alt,az,roll = expected_aar(loc)
    fudge_altaz = im[7]
    alt = alt+rad(fudge_altaz[0])
    az = az+rad(fudge_altaz[1])
    if not (tree_roll(im) is None):
      roll = tree_roll(im)
    print "    azimuth=",deg(az),", alt=",deg(alt),", roll=",deg(roll),"  distance=",dist/1000.0," km"
    fit_in,fit_out = gather_in_and_out_for_fit(dat,im)
    method = 2
    if method==1:
      perspective = Ortho(alt,az,roll)
    if method==2:
      o = Ortho(alt,az,roll)
      perspective = Point(o,loc)
    perspective.fit(fit_in,fit_out)
    pr[label] = perspective
    print "  ",perspective
  #------------ 
  print "Calculating errors:"
  for im in images:
    label = im[0]
    if not (label in pr):
      continue
    print "  ",label
    perspective = pr[label]
    i_obs = []
    j_obs = []
    i_pred = []
    j_pred = []
    for obs in dat:
      p,im2,ij = obs
      if im2!=im:
        continue
      if p["p"] is None:
        continue
      descr = p["name"]+", "+p["description"]
      gps = p["p"]
      pred = perspective.apply(gps)
      err = [None,None]
      err[0] = pred[0]-ij[0]
      err[1] = pred[1]-ij[1]
      i_obs.append(ij[0])
      j_obs.append(ij[1])
      i_pred.append(pred[0])
      j_pred.append(pred[1])
      print "    obs=(%4d,%4d), pred=(%4d,%4d), err=(%4d,%4d) %s" % (ij[0],ij[1],pred[0],pred[1],err[0],err[1],descr)
    do_svg_error_arrows(im[0],im[4],find_image_file(im[1]),i_obs,j_obs,i_pred,j_pred)

def gather_in_and_out_for_fit(dat,im):
  fit_in = []
  fit_out = []
  for obs in dat:
    p,im2,ij = obs
    if im2!=im:
      continue
    if p["p"] is None:
      continue
    gps = p["p"]
    fit_in.append(gps)
    fit_out.append(ij)
  return [fit_in,fit_out]

def altaz_pars_to_str(x,printing_funcs):
  xp = []
  for i in range(len(x)):
    xp.append(printing_funcs[i](x[i]))
  return str(xp)

def pix(dat,p,im,i,j):
  # (i,j) = pixel coordinates with respect to top left (the convention used in gimp)
  dat.append([p,im,[float(i),float(j)]])

def image(list,label,filename,loc=None,loc_err=None,is_satellite=False,tree_roll=None,fudge_altaz=[0.0,0.0]):
  # The optional loc argument is the UTM coords of the camera, and loc_err=[x,y] is an estimate of the possible error in the horizontal coordinates.
  # The parameter tree_roll is to fix the roll parameter. If the trees lean left by 3 degrees, this parameter is 3. Often the lean of the trees
  # various obviously from left to right, a sign of aberration/projection; if so, then this is the estimate of the angle near the center of the field.
  w,h = [get_image_size(filename,'w'),get_image_size(filename,'h')]
  if not (tree_roll is None):
    tree_roll = rad(tree_roll)
  else:
    tree_roll = 0.0
  im = [label,filename,utm_input_convenience(loc),loc_err,[w,h],is_satellite,tree_roll,fudge_altaz]
  list.append(im)
  return im

def is_satellite(im):
  return im[5]

def tree_roll(im):
  return im[6]

def get_image_size(filename,dim):
  # dim can be 'w' or 'h'
  cached_sizes = {
    "01_northeast_from_saddle_jct":[3077, 5357],
    "05_north_side_from_saddle_jct":[4512, 3664],
    "10_north_face_from_old_devils_slide_trail":[5280, 4720],
    "15_panorama_from_low_on_devils_slide":[11885, 6500],
    "17_north_and_northwest_sides_from_strawberry_cienega":[8943,7007],
    "19_northwest_side_from_deer_springs_boulder_pile":[4896,3264],
    "20_northwest_face_from_deer_springs_slabs":[3264, 4896],
    "25_northwest_face_from_suicide_junction":[2720, 4592],
    "30_from_fern_valley":[2723, 2447],
    "35_tahquitz_rock_from_pine_cove_ca":[3096, 4096],
    "40_west_side_from_auto_parts_store":[3157, 2983],
    "50_south_face_from_bottom_of_maxwell_trail":[3586, 3554],
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
