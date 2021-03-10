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

#Complete
- UNDO ctrl-z (REDO ctrl-y)
- Extensible parts library
- Intuative zoom
- Intuative alignment

#TODO
- Incorporate pricing CSV to easily change prices
- add more parts
- Get interfaces working

# Development Videos
## Introduction 
[![Intro](https://img.youtube.com/vi/FModxybh0cM&t=11s/0.jpg)](https://www.youtube.com/watch?v=FModxybh0cM&t=11s)

## Alignment Demo
[![Quick Demo](https://img.youtube.com/vi/UnlkdmXvXzY/0.jpg)](https://www.youtube.com/watch?v=UnlkdmXvXzY)
## New Part Demo
[![New Part Demo](https://img.youtube.com/vi/-pqmj2yvioE/0.jpg)](https://youtu.be/-pqmj2yvioE)


# Thanks to
pyquaternion: https://github.com/KieranWynn/pyquaternion for providing a python library that is easy to include with Alex.
