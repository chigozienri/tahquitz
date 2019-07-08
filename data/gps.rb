#!/usr/bin/ruby

require_relative 'util_gps'
require_relative 'dem'

# In the following, I throw away the results, so all that happens is a sanity check.

def main()
  gps(440,435,7238,NAD27,'uneventful',1,'first big pine tree; y is not possible')
  gps(444,519,7465,NAD27,'uneventful',2,'second big pine tree; y is not possible')
  # no gps reception at belay 3
  gps(445,466,7634,NAD27,'uneventful',4,'left side of big J tree ledge')
  #
  gps(222,675,7405,NAD83,'fools_rush',1,'huge ledge')
  gps(255,663,7645,NAD83,'fools_rush',2,'oak tree ledge above crux')
  gps(272,638,7761,NAD83,'fools_rush',3,'saddle-shaped ledge next to 3rd belay on Maiden; z probably too high by ca. 60 ft')
  gps(271,632,7873,NAD83,'fools_rush',4,'just below 5th belay on Maiden, slightly lower than shown on my topo of Fools Rush ')
  gps(271,638,7969,NAD83,'fools_rush',5,'top of 5.3 variation of Maiden; x should be lower')
  #
  gps(304,771,2202,NAD83,'error',0,'very bottom of rock')
  gps(320,738,2231,NAD83,'error',1,'on top of boulder, next to rusty bolt, above pine tree on left')
  gps(327,730,2240,NAD83,'error',2,'ledge under overhangs')
  gps(328,715,2270,NAD83,'error',3,'middle (?) of rubble-strewn ledge')
  gps(336,694,2295,NAD83,'error',4,'alcove')
  gps(352,679,2333,NAD83,'error',5,'near mountain mahogany trees, where the climbing gets easier and the ledge starts to develop')
  #gps(,NAD83,'error',0,'')

  x,y,z = summit_position()
  print "DEM gives summit elevation = #{dem(x,y)}, should be #{z}\n"
end

def gps(x,y,elevation,datum,route,belay,description)
  c = raw_to_cooked(elevation,x,y,datum,route,belay,description)
  if c[0] then
    $stderr.print "Error processing input GPS point, #{description}: #{c[1]}\n"
    exit(-1)
  end
  data = c[2]
  dem_elevation = dem(x,y)
  print (sprintf "%3d %3d %3d z-DEM=%4d %20s %1d %s",round(data['x']),round(data['y']),round(data['elevation']),round(data['elevation']-dem_elevation),data['route'],data['belay'],data['description']),"\n"
end

def round(x)
  return (x+0.5).to_i
end

main


