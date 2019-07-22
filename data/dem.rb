# This is rickety and crappy. Shound do something more robust.
# See, e.g., https://gis.stackexchange.com/questions/29632/getting-elevation-at-lat-long-from-raster-using-python
# Treatment of (x,y) is wrong, because I assumed that the pixels were aligned exactly with my box, but they aren't.
# Need to read the header from the .aig file.

def dx()
  return 25.649 # width of cell in meters, see Makefile for how this was found
end

def dy()
  return 30.899 # height of cell in meters, see Makefile for how this was found
end

def nrows()
  return 32 # comes from headers in .aig file
end

def ncols()
  return 39 # comes from headers in .aig file
end

def dem(x,y)
  # x and y are in meters, relative to lower-left corner of the 1-km UTM/NAD83 square containing Tahquitz
  # To use this from the command line:
  #  ruby -e "require './dem'; print dem(10,10)"
  xx = x/dx()
  yy = y/dy()
  # Consider the four cells whose centers are closest to this point. First find the col and row of the lower left one.
  i = xx.to_i
  j = yy.to_i
  #print "x=#{x}, y=#{y}, xx=#{xx}, yy=#{yy}, i=#{i}, j=#{j}\n" # qwe
  z00 = get_elevation(i,j)
  z10 = get_elevation(i+1,j)
  z01 = get_elevation(i,j+1)
  z11 = get_elevation(i+1,j+1)
  return interpolate_square(xx-i,yy-j,z00,z10,z01,z11)
end

def interpolate_square(x,y,z00,z10,z01,z11)
  if z00.nil? or z10.nil? or z01.nil? or z11.nil? then return nil end
  # https://en.wikipedia.org/wiki/Bilinear_interpolation#Unit_Square
  # The crucial thing is that this give results that are continuous across boundaries of squares.
  w00 = (1.0-x)*(1.0-y)
  w10 = x*(1.0-y)
  w01 = (1.0-x)*y
  w11 = x*y
  norm = w00+w10+w01+w11
  z = (z00*w00+z10*w10+z01*w01+z11*w11)/norm
  return z
end

def get_elevation(i,j)
  # Input file is created by Makefile.
  File.open('tahquitz.aig','r') { |f|
    row = 0
    f.each_line { |line|
      next if !(line=~/\A\s(.*)/) # actual data lines start with whitespace; header lines don't
      numbers = $1.split(/\s+/).map { |z| z.to_f} 
      # Rows in file are northernmost first, i.e., descending y.
      # I think the following condition should logically be row==nrows()-j-1, but empirically omitting the -1 is what seems to give the
      # right point for the summit of Tahquitz.
      if row==nrows()-j then # rows in file are northernmost first, i.e., descending y
        n = numbers
        return n[i].to_f
      end
      row = row+1
    }
  }
  return nil
end

