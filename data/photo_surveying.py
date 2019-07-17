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
  im05 = image(images,"05","05_north_side_from_saddle_jct")
  im10 = image(images,"10","10_north_face_from_old_devils_slide_trail")
  im15 = image(images,"15","15_panorama_from_low_on_devils_slide")

  p = point("uneventful-4",366,662,2327,"left side of big J tree ledge")
  pix(dat,p,im01,1775,2130)
  pix(dat,p,im05,1967,1671)
  pix(dat,p,im10,2284,1675)

  p = point("summit",347.0,623.0,2439.0,"summit")
  pix(dat,p,im01,2010,326)
  pix(dat,p,im05,2145,360)
  pix(dat,p,im10,2493,280)

  p = point("error-2",327,730,2240,"ledge under overhangs; left-right position uncertain by a few meters")
  pix(dat,p,im01,2791,3923)
  pix(dat,p,im05,2560,2925)
  pix(dat,p,im10,3128,3072)
  pix(dat,p,im15,4322,4786)

  p = point("error-3",328,715,2270,"middle (?) of rubble-strewn ledge")
  pix(dat,p,im01,2542,3434)
  pix(dat,p,im05,2442,2580)
  pix(dat,p,im10,2933,2701)
  pix(dat,p,im15,4232,4211)

  p = point("error-4",336,694,2295,"alcove before steep part; poor agreement between photo surveying and GPS")
  pix(dat,p,im01,2329,3024)
  pix(dat,p,im05,2319,2301)
  pix(dat,p,im10,2755,2380)
  pix(dat,p,im15,4195,3818)

  p = point("north-buttress-1",341,750,2230,"upper pine tree")
  pix(dat,p,im01,2637,4318)
  pix(dat,p,im05,2533,3198)
  pix(dat,p,im15,3368,5057)

  p = point("west-lark-0",388,797,2174,"base of rock; is the same location as the start of the other larks")
  pix(dat,p,im01,2065,5280)

  p = point("maiden-0",250,700,2248,"tree root on class 3 ledge, before the hard mantling move")
  pix(dat,p,im05,3131,2841)
  pix(dat,p,im10,4021,3010)

  p = point("maiden-1",245,698,2277,"mountain mahogany (could be wrong)")
  pix(dat,p,im05,3109,2476)
  pix(dat,p,im10,3965,2604)
  pix(dat,p,im15,6839,4171)

  return [images,dat]

def analyze():
  images,dat = init()
  coeff = {}
  for im in images:
    label = im[0]
    #print im[1] # filename
    c = [] # coefficients for this image
    for coord in range(2): # 0=i=horizontal coord of pixel in image, 1=j=vertical (from top)
      #print "  coord=",coord
      x_list = []
      y_list = []
      for obs in dat:
        p,im2,ij = obs
        if im2!=im:
          continue
        y = ij[coord]
        x = p["p"]
        descr = p["description"]
        #print "    x=",x,"  y=",y,"   ",descr
        x_list.append(x)
        y_list.append(y)
      # https://stackoverflow.com/a/11479279/1142217
      clf = linear_model.LinearRegression(fit_intercept=True)
      clf.fit(x_list,y_list)
      #print "    ",clf.coef_," ",clf.intercept_
      c.append([copy.copy(clf.coef_),copy.copy(clf.intercept_)])
    coeff[label] = c
  sum_sq = 0.0
  n = 0
  for im in images:
    label = im[0]
    print im[1] # filename
    c = coeff[label]
    for obs in dat:
      p,im2,ij = obs
      descr = p["name"]+", "+p["description"]
      if im2!=im:
        continue
      obs = []
      pred = []
      err = []
      for coord in range(2):
        co_obs = ij[coord]
        gps = p["p"]
        co_pred = c[coord][1]
        for m in range(3):
          co_pred = co_pred + c[coord][0][m]*gps[m]
        obs.append(co_obs)
        pred.append(co_pred)
        err.append(co_pred-co_obs)
        n = n+1
        sum_sq = sum_sq+(co_pred-co_obs)*(co_pred-co_obs)
      print "  obs=(%4d,%4d), pred=(%4d,%4d), err=(%4d,%4d) %s" % (obs[0],obs[1],pred[0],pred[1],err[0],err[1],descr)
      #print "  obs=",obs,"  pred=",pred,"  ",p["description"]
  print "n=",n,"  rms error=",math.sqrt(sum_sq/n)

def pix(dat,p,im,i,j):
  # (i,j) = pixel coordinates with respect to top left (the convention used in gimp)
  dat.append([p,im,[float(i),float(j)]])

def image(list,label,filename):
  im = [label,filename]
  list.append(im)
  return im

def point(name,x,y,z,description):
  # Define a new point on the rock, such as a belay, but its UTM coordinates (NAD83).
  # Coordinates are in meters, relative to (529 km,3735 km) in zone 11S.
  return {"name":name,"p":[float(x),float(y),float(z)],"description":description}

main()
