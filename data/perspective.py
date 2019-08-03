from geom import *

class Perspective:
  def __init__(self):
    if type(self) is Base:
      raise Exception('Perspective is an abstract class and cannot be instantiated directly')

  def apply(self,xyz):
    # returns [i,j], throwing away k
    ij = self.apply3(xyz)
    return [ij[0],ij[1]]

  def fit(self,fit_in,fit_out,what=0):
    # fit_in = list of xyz coords of points
    # fit_out = list of ij coords of pixels that we want those to map to
    # what = 0 to fit both scale and translation, 1 for scale (to be done first), 2 for translation
    if len(fit_in)<2:
      raise Exception('need at least two points')
    if what==0:
      self.fit(fit_in,fit_out,what=1)
      self.fit(fit_in,fit_out,what=2)
      return
    i0 = [] # list of i coords that we would currently produce
    j0 = []
    i1 = [] # list of i coords that we would like to produce
    j1 = []
    for m in range(len(fit_in)):
      i,j = self.apply(fit_in[m])
      i0.append(i)
      j0.append(j)
      out = fit_out[m]
      i1.append(out[0])
      j1.append(out[1])
    if what==1: # scale only
      s = math.sqrt((std_dev(i1)**2+std_dev(j1)**2)/(std_dev(i0)**2+std_dev(j0)**2))
      self.rescale(s)
      return
    if what==2: # translation only
      self.translate([avg(i1)-avg(i0),avg(j1)-avg(j0),0.0])
      return
    raise Exception('huh? is what set wrong in fit()?')

class Point(Perspective):
  # A view from a point. The projection consists of projecting the image point through the fixed point (iris of the lens) to a fixed plane.
  # We describe this using an Ortho (with 0 translation, no rescaling needed), a location, and a final scaling and translation.
  # To construct one of these, construct the Ortho (but don't fit), then call this constructor, then fit.
  def __init__(self,ortho,loc):
    self.ortho = ortho
    self.loc = loc
    self.scale = 1.0
    self.trans = [0.0,0.0]

  def __str__(self):
    return str(self.ortho)+"\n"+("loc=%9.4f %9.4f %9.4f" % (self.loc[0],self.loc[1],self.loc[2]))

  def apply(self,xyz):
    # override class method; 3rd component wouldn't make sense, so no apply3()
    # returns None if point is in or behind image plane
    los = sub_vectors(xyz,self.loc) # line of sight from camera to point
    i0,j0,k0 = self.ortho.apply3(los)
    if k0<=0.0:
      return None
    i = self.scale*i0/k0+self.trans[0]
    j = self.scale*j0/k0+self.trans[1]
    return [i,j]

  def rescale(self,s):
    self.scale *=s

  def translate(self,d):
    for m in range(2):
      self.trans[m] += d[m]

class Ortho(Perspective):
  # A view from an infinite distance, with no vanishing points. This is simply projection onto a plane, followed by a scaling and translation.
  # After calling the constructor, the scaling and translation are not yet set properly. These need to be set using the fit() method.
  def __init__(self,alt,az,roll):
    a = rotation_matrix(alt,az-math.pi/2.0,roll) # subtract 90 from az, because line of sight is z, so when az=0, x is south
    ic = [a[0][0],a[1][0],a[2][0]] # camera's basis vector pointing to the right
    jc = [a[0][2],a[1][2],a[2][2]] 
    jc = scalar_mult(jc,-1.0) # camera's basis vector pointing down; pixel coordinates in the vertical direction are increasing downward
    kc = [a[0][1],a[1][1],a[2][1]] # camera's basis vector pointing in the direction you're looking
    # coefficients of the affine transformation from (x,y,z) to (i,j,k):
    self.c = [
      [ic,0.0],
      [jc,0.0],
      [kc,0.0]
    ]

  def __str__(self):
    return str("%9.4f %9.4f %9.4f | %9.4f\n%9.4f %9.4f %9.4f | %9.4f\n%9.4f %9.4f %9.4f | %9.4f " % (
      self.c[0][0][0],self.c[0][0][1],self.c[0][0][2],self.c[0][1],
      self.c[1][0][0],self.c[1][0][1],self.c[1][0][2],self.c[1][1],
      self.c[2][0][0],self.c[2][0][1],self.c[2][0][2],self.c[2][1]
    ))

  def apply3(self,xyz):
    # returns [i,j,k]
    if len(xyz)!=3:
      raise Exception('xyz has wrong number of coordinates')
    ij = []
    for coord in range(3):
      co_pred = self.c[coord][1]
      for m in range(3):
        co_pred = co_pred + self.c[coord][0][m]*xyz[m]
      ij.append(co_pred)
    return ij

  def rescale(self,s):
    for m in range(2):
      for n in range(3):
        self.c[m][0][n] = self.c[m][0][n]*s

  def translate(self,d):
    for m in range(3):
      self.c[m][1] += d[m]




    
