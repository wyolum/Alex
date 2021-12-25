import glob
import sys
import os
from distutils import spawn

mm = 1
inch = 25.4
units = {'mm':mm,
         'inch': inch}
pi = 3.141592653589793
DEG = pi / 180.

fine_rotation_angle = 1/18.

package_dir = os.path.split(os.path.abspath(__file__))[0]
alex_scad = os.path.join(package_dir, '../', 'Alex_test.scad')
stl_dir = os.path.join(package_dir, 'STL')
npy_dir = os.path.join(package_dir, 'wireframes')
scripts_dir = os.path.split(package_dir)[0]
alex_dir = os.path.split(scripts_dir)[0]
part_libraries_dir = os.path.join(alex_dir, 'part_libraries')

openscad_path = spawn.find_executable('openscad')
if openscad_path is None:
    if sys.platform == 'darwin':
        option_press = '<ButtonPress-2>'

        for root, dirs, files in os.walk('/Applications/OpenSCAD.app', topdown = False):
            for file in files:
                if file.lower() == "openscad":
                    openscad_path = f'{root}/{file}'
                    break
        else:
            openscad_path = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
    else:
        option_press = '<ButtonPress-3>'
        
# print('openscad_path', openscad_path)
bgcolor = "white"
hlcolor = '#0432ff' ## Blueberry

