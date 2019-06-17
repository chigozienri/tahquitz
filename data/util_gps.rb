NAD27 = 1
NAD83 = 2

def raw_to_cooked(elevation,x,y,datum,route,belay,description)
  # elevation: can be either in feet or meters, disambiguated by a sanity check
  # x,y: UTM easting and northing, in meters, relative to 11S 0529,000 3735,000
  # datum: must be NAD27 or NAD83
  # route: should be a string that is the same as the base of the filename for the topo; null string if not a
  #        climbing route
  # belay: 0=start of climb; ignored if route is null
  # description: e.g., big pine tree
  # Inputs can be ints or floats.
  # Returns a [err,message,hash].
  # Hash has keys "elevation", etc. (all except for "datum").
  # UTM coords are converted to NAD83. Elevation is converted to meters
  if !sane_elevation(elevation,false) && sane_elevation(feet_to_meters(elevation),false) then
    elevation = feet_to_meters(elevation)
  end
  if !sane_elevation(elevation,false) then
    return [true,'elevation fails sanity check',{}]
  end
  if x>10000.0 then
    return [true,'UTM coordinates should be given in meters, relative to 11S 0529,000 3735,000',{}]
  end
  result = {}
  if route!='' then
    # stricter sanity check for something that claims to be a point on a climbing route
    if !sane_elevation(elevation,true) then
      return [true,'elevation is not sane for a point on a climbing route',{}]
    end
    if !(x>=150 && x<=680) then
      return [true,'UTM x is not sane for a point on a climbing route',{}]
    end
    if !(y>=260 && y<=650) then
      return [true,'UTM y is not sane for a point on a climbing route',{}]
    end
    result['route'] = route
    result['belay'] = belay
  else
    result['route'] = ''
    result['belay'] = -1
  end
  if !(datum==NAD27 || datum==NAD83) then
    return [true,'datum must be NAD27 or NAD83',{}]
  end
  if datum==NAD27 then
    # Ran an example to determine the offset (belay 1, pine tree, on The Uneventful).
    # NAD 27 = 11S 0529440 3735485
    # NOAA conversion of lat-lon from NAD83 to NAD27 gives
    #   NAD 27 - NAD 83 shift values: lat = -2.256, lon = -78.843  (meters)
    #   the lon is west, so flip sign
    x = x-78.843
    y = y+2.256
  end
  result['elevation'] = elevation.to_f
  result['x'] = x.to_f
  result['y'] = y.to_f
  result['description'] = description
  return [false,nil,result]
end

def sane_elevation(meters,is_a_route)
  idyllwild = 1650 # meters
  bottom_of_rock = 2194 # 7200'; hundreds of feet lower than the start of any route
  top_of_rock = 2334 # meters
  if is_a_route then
    return (meters>bottom_of_rock && meters<top_of_rock+100)
  else
    return (meters>idyllwild && meters<top_of_rock+100)
  end
end

def feet_to_meters(ft)
  return 0.3048*ft
end
