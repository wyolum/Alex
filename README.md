# Alex
Aluminium Extrusion specific CAD program for Python3
```
> pip install numpy
> git clone git@github.com:wyolum/Alex.git
> cd Alex/scripts
> touch Alex_test.scad ## or wait for AlexCAD to generate this automatically
> openscad Alex_test.scad & ### background this task or launch OpenScad manually, file->open "Alex_test.scad"'
>                           ### in the OpenScad menu select Design->Automatically Reload and Preview
> python main_06.py
```

[![Quick Demo](https://img.youtube.com/vi/mkjgiLznFwk/0.jpg)](https://www.youtube.com/watch?v=mkjgiLznFwk)

## Shortcuts
* ctrl-n -- New Aluminum Extrusion
* ctrl-g -- Group selected items
* ctrl-u -- Ungroup selected group
* ctrl-d -- Duplicated selected items
* Del    -- Delete selected object

![GitHub Logo](images/screenshot.png)

#TODO
- UNDO ctrl-z
- Incorporate pricing CSV to easily change prices
- Add new parts
- Allow recentering (right now only one center allowed)
- Get interfaces working


# Thanks to
pyquaternion: https://github.com/KieranWynn/pyquaternion for providing a python library that is easy to include with Alex.
