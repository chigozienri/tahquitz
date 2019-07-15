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

  # july 11, hike with dogs
  # There are two north gully trails. There is a fork on the way up. We always go right on the way up (more obvious).
  # This takes you to the main junction (in front of the dark wall, what I'cve beenthinkingh og as the junction.)
  # and the climbing areas. This goes through some talus.
  # We never go left. Thi s is more like the descent trail. It avoids the talus.
  # So there is really a triangle of trails, with three junctions.
  # Times below are from watch, arer about 1 min ahead ogf Pi's cloclk.
  # 18:12 trailhead
  # 18:25 enter oak grove
  # 18:48 "the" jct, 574 777 2134
  # 18:56 foot of class 4 gully that starts below and to right of el whampo and leads tyo it, 510 782 2163
  # 18:59 on trail, lined up with NE Face E diheadral 439 786 2158
  # 19:03 on trail bvelow larks, 394 795 2181
  # 19:06 larks, base of rock 388 797 2174
  # 19:11 uneventful, talus exactly at base of rock 346 783 2185
  # 19:19 the error, at base of rock, 304 768 2197
  # 19:39 entering oak grove on the way dfown
  # 19:47 car at north gully TH 086 092 1992
  #
  # july 12, fri, north buttress with matt
  # until 8:37 ground anchor on boulder, 332 781 2188
  # 9:14 first belay at upper pine tree 335 752 2234
  # third belay 11:30 (big lefge below arches)
  # fourth belay, at top of right-hand dihedral,lower than first time
  # ~14:05 arrive at J tree ledge
  # turned off gps
  # reactivated gps, I think at endof class 3 ledge (not earlier at trees)

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


