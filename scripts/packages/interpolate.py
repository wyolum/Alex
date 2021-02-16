'''
source: http://www.astropython.org/snippets/interpolation-without-scipy90/
'''

import numpy

def interp1d(xin, yin, xout, method='linear'):
  """
  Interpolate the curve defined by (xin, yin) at points xout. The array
  xin must be monotonically increasing. The output has the same data type as
  the input yin.

  :param yin: y values of input curve
  :param xin: x values of input curve
  :param xout: x values of output interpolated curve
  :param method: interpolation method ('linear' | 'nearest')

  @:rtype: numpy array with interpolated curve
  """
  lenxin = len(xin)

  i1 = numpy.searchsorted(xin, xout)

  if i1 == 0:
    i1 = 1
  if i1 == lenxin:
    i1 = lenxin-1

  x0 = xin[i1-1]
  x1 = xin[i1]
  y0 = yin[i1-1]
  y1 = yin[i1]

  if method == 'linear':
    return (xout - x0) / (x1 - x0) * (y1 - y0) + y0
  elif method == 'nearest':
    return numpy.where(numpy.abs(xout - x0) < numpy.abs(xout - x1), y0, y1)
  else:
    raise ValueError('Invalid interpolation method: %s' % method)# Python code here

