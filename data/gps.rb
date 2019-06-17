#!/usr/bin/ruby

require_relative 'util_gps'

# In the following, I throw away the results, so all that happens is a sanity check.

def main()
  gps(7238,440,435,NAD27,'uneventful',1,'first big pine tree; difference in elevation from belay 2 is not possible')
  gps(7465,444,519,NAD27,'uneventful',2,'second big pine tree; difference in elevation from belay 1 is not possible')
  # no gps reception at belay 3
  gps(7634,445,466,NAD27,'uneventful',4,'left side of big J tree ledge')
end

def gps(elevation,x,y,datum,route,belay,description)
  c = raw_to_cooked(elevation,x,y,datum,route,belay,description)
  if c[0] then
    $stderr.print "Error processing input GPS point, #{description}: #{c[1]}"
    exit(-1)
  end
  data = c[2]
  print (sprintf "%4d %3d %3d %20s %1d %s",round(data['elevation']),round(data['x']),round(data['y']),data['route'],data['belay'],data['description']),"\n"
end

def round(x)
  return (x+0.5).to_i
end

main


