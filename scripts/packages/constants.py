import os
from distutils import spawn

mm = 1
inch = 25.4
units = {'mm':mm,
         'inch': inch}
pi = 3.141592653589793
DEG = pi / 180.


package_dir = os.path.split(os.path.abspath(__file__))[0]
alex_scad = os.path.join(package_dir, '../', 'Alex_test.scad')
stl_dir = os.path.join(package_dir, 'STL')
npy_dir = os.path.join(package_dir, 'wireframes')


openscad_path = spawn.find_executable('openscad')

bgcolor = "white"
hlcolor = '#0432ff' ## Blueberry

