module square_bar(l, d1){
  color("silver")linear_extrude(l)
    scale(d1/30)import(file = "../resources/30-30.dxf");
}

module bar(l, d1, d2){
  translate([0, d1/2 - d2/2, 0])
  for (i = [0:d2/d1-1]){
    translate([0, i * d1, 0])square_bar(l, d1);
  }
}

module corner_two_way(d1){
    scale(d1/20)color([.3, .3, .3])
        rotate([0, 0, 90])translate([-10, -10, 0])
        import("../STL/Black_Angle_Corner_Connector.STL");
}
module corner_three_way(d1){
    color([.3, .3, .3])
      {
	translate([-d1/2, -d1/2, 0])cube([d1, d1, 5]);
	translate([-d1/4, -d1/4, 2])cube([d1/2, 1.25 * d1, 1]);
	translate([-d1/8, -d1/4, 0])cube([d1/4, 1.25 * d1, 2]);
	rotate([0, 0, 90])translate([-d1/4, -d1/4, 2])cube([d1/2, 1.25 * d1, 1]);
	rotate([0, 0, 90])translate([-d1/8, -d1/4, 0])cube([d1/4, 1.25 * d1, 2]);
	translate([d1/2-2, -d1/4, 0])cube([1, d1/2, .75*d1]);
	translate([d1/2-2, -d1/8, 0])cube([2, d1/4, .75*d1]);
	rotate([0, 0, -90])translate([d1/2-2, -d1/4, 1])cube([1, d1/2, .75*d1]);
	rotate([0, 0, -90])translate([d1/2-2, -d1/8, 1])cube([2, d1/4, .75*d1]);
	/*
	 */
      }
}
module corner_three_way_left(d1){
  mirror([1, 0, 0])corner_three_way(d1);
}
  

