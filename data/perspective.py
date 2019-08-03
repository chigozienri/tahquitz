from geom import *

class Perspective:
  def __init__(self):
    if type(self) is Base:
      raise Exception('Perspective is an abstract class and cannot be instantiated directly')

class Ortho:
  # A view from an infinite distance, with no vanishing points. This is simply projection onto a plane, followed by a scaling and translation.
  # After calling the constructor, the scaling and translation are not yet set properly. These need to be set using the fit() method.
  def __init__(self,alt,az,roll):
    a = rotation_matrix(alt,az-math.pi/2.0,roll) # subtract 90 from az, because line of sight is z, to when az=0, x is south
    vs = -1.0 # pixel coordinates in the vertical direction are increasing downward
    ic = [a[0][0],a[1][0],a[2][0]] # camera's basis vector pointing to the right
    jc = [a[0][1],a[1][1],a[2][1]] # camera's basis vector pointing up
    # coefficients of the affine transformation from (x,y,z) to (i,j):
    self.c = [
      [                ic,0.0],
      [scalar_mult(jc,vs),0.0]
    ]

  def apply(self,xyz):
    if len(xyz)!=3:
      raise Exception('xyz has wrong number of coordinates')
    ij = []
    for coord in range(2):
      co_pred = self.c[coord][1]
      for m in range(3):
        co_pred = co_pred + self.c[coord][0][m]*xyz[m]
      ij.append(co_pred)
    return ij

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
      for m in range(2):
        for n in range(3):
          self.c[m][0][n] = self.c[m][0][n]*s
      return
    if what==2: # translation only
      self.c[0][1] = avg(i1)-avg(i0)
      self.c[1][1] = avg(j1)-avg(j0)
      return
    raise Exception('huh? is what set wrong in fit()?')



    
