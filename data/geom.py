import copy,math

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

