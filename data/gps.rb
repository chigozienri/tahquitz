#!/usr/bin/ruby

require_relative 'util_gps'
require_relative 'dem'

# In the following, I throw away the results, so all that happens is a sanity check and a printout.

def main()
  gps(346,783,2185,NAD83,'uneventful',0,'talus exactly at base of rock; from hike with dogs')
  #gps(440,435,7238,NAD27,'uneventful',1,'first big pine tree; y and z both not possible')
  #gps(444,519,7465,NAD27,'uneventful',2,'second big pine tree; y is not possible')
  # no gps reception at belay 3
  gps(445,466,7634,NAD27,'uneventful',4,'left side of big J tree ledge')
  #
  gps(222,675,7405,NAD83,'fools_rush',1,'huge ledge')
  gps(255,663,7645,NAD83,'fools_rush',2,'oak tree ledge above crux')
  gps(272,638,7761,NAD83,'fools_rush',3,'saddle-shaped ledge next to 3rd belay on Maiden; z probably too high by ca. 60 ft')
  gps(271,632,7873,NAD83,'fools_rush',4,'just below 5th belay on Maiden, slightly lower than shown on my topo of Fools Rush ')
  gps(271,638,7969,NAD83,'fools_rush',5,'top of 5.3 variation of Maiden; x should be lower')
  #
  gps(304,770,2200,NAD83,'error',0,'very bottom of rock; average of data from two different days, consistent to a few meters')
  gps(320,738,2231,NAD83,'error',1,'on top of boulder, next to rusty bolt, above pine tree on left')
  gps(327,730,2240,NAD83,'error',2,'ledge under overhangs')
  gps(328,715,2270,NAD83,'error',3,'middle (?) of rubble-strewn ledge')
  gps(336,694,2295,NAD83,'error',4,'alcove; poor agreement between photo surveying and GPS')
  gps(352,679,2333,NAD83,'error',5,'near mountain mahogany trees, where the climbing gets easier and the ledge starts to develop')
  #gps(,NAD83,'error',0,'')

  # 2019 july 12, north buttress with matt
  gps(327,783,2189,NAD83,'north_buttress',0,'ground anchor on top of boulder')
  gps(341,750,2230,NAD83,'north_buttress',1,'upper pine tree')
  gps(345,721,2255,NAD83,'north_buttress',2,'probably left side of ledge')
  gps(348,700,2298,NAD83,'north_buttress',3,'large ledge across from alcove on The Error')

  # 2019 july 14, maiden with lara
  gps(250,700,2248,NAD83,'maiden',0,'tree root on class 3 ledge, before the hard mantling move')
  gps(245,698,2277,NAD83,'maiden',1,'mountain mahogany (could be wrong)')

  # 2019 july 11, hike with dogs
  gps( 86,1104,1986,NAD83,'',-1,'North Gully trailhead at Humber Park')  
  gps(328,1039,2068,NAD83,'',-1,'bottom of oak grove on North Gully Trail')
  gps(427,990,2098,NAD83,'',-1,'top of oak grove on North Gully Trail (?)')
  gps(574,777,2134,NAD83,'',-1,'junction of North Gully ascent trail at rock wall')
  gps(388,797,2174,NAD83,'west_lark',0,'base of rock; is the same location as the start of the other larks')
  gps(510,782,2163,NAD83,'el_whampo',0,'foot of class 4/easy 5th gully that is the first easy pitch of El Whampo')
  #gps(439,786,2158,NAD83,'northeast_face_east',0,'trail directly below the dihedral')
  # ... this seems wildly off in x in satellite image; I think this may have been NE face W rather than NE face E

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
  if dem_elevation.nil? then
    dem_err = -999
  else
    dem_err = data['elevation']-dem_elevation
  end
  print (sprintf "%3d %3d %3d z-DEM=%4d %20s %1d %s",round(data['x']),round(data['y']),round(data['elevation']),round(dem_err),data['route'],data['belay'],data['description']),"\n"
end

def round(x)
  return (x+0.5).to_i
end

main


