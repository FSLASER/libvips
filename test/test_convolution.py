#!/usr/bin/python3

from __future__ import division
from builtins import zip
from builtins import range
from numbers import Number

import unittest
import math

#import logging
#logging.basicConfig(level = logging.DEBUG)

from gi.repository import Vips 

# an expanding zip ... if either of the args is a scalar or a one-element list,
# duplicate it down the other side 
def zip_expand(x, y):
    # handle singleton list case
    if isinstance(x, list) and len(x) == 1:
        x = x[0]
    if isinstance(y, list) and len(y) == 1:
        y = y[0]

    if isinstance(x, list) and isinstance(y, list):
        return list(zip(x, y))
    elif isinstance(x, list):
        return [[i, y] for i in x]
    elif isinstance(y, list):
        return [[x, j] for j in y]
    else:
        return [[x, y]]

# run a 1-ary function on a thing -- loop over elements if the 
# thing is a list
def run_fn(fn, x):
    if isinstance(x, list):
        return [fn(i) for i in x]
    else:
        return fn(x)

# run a 2-ary function on two things -- loop over elements pairwise if the 
# things are lists
def run_fn2(fn, x, y):
    if isinstance(x, Vips.Image) or isinstance(y, Vips.Image):
        return fn(x, y)
    elif isinstance(x, list) or isinstance(y, list):
        return [fn(i, j) for i, j in zip_expand(x, y)]
    else:
        return fn(x, y)

# point convolution
def conv(image, mask, x_position, y_position):
    s = 0.0
    for x in range(0, mask.width):
        for y in range(0, mask.height):
            m = mask.getpoint(x, y)
            i = image.getpoint(x + x_position, y + y_position)
            p = run_fn2(lambda a, b: a * b, m, i)
            s = run_fn2(lambda a, b: a + b, s, p)

    return run_fn2(lambda a, b: a / b, s, mask.get_scale())

class TestConvolution(unittest.TestCase):
    # test a pair of things which can be lists for approx. equality
    def assertAlmostEqualObjects(self, a, b, places = 4, msg = ''):
        #print 'assertAlmostEqualObjects %s = %s' % (a, b)
        for x, y in zip_expand(a, b):
            self.assertAlmostEqual(x, y, places = places, msg = msg)

    def setUp(self):
        im = Vips.Image.mask_ideal(100, 100, 0.5, reject = True, optical = True)
        self.colour = im * [1, 2, 3] + [2, 3, 4]
        self.mono = self.colour.extract_band(1)
        self.all_images = [self.mono, self.colour]
        sharp = Vips.Image.new_from_array([[-1, -1,  -1], 
                                           [-1,  16, -1], 
                                           [-1, -1,  -1]], scale = 8)
        blur = Vips.Image.new_from_array([[1, 1, 1], 
                                          [1, 1, 1], 
                                          [1, 1, 1]], scale = 9)
        line = Vips.Image.new_from_array([[1, 1, 1], [-2, -2, -2], [1, 1, 1]])
        sobel = Vips.Image.new_from_array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
        self.all_masks = [sharp, blur, line, sobel]

    def test_conv(self):
        for im in self.all_images:
            for msk in self.all_masks:
                for prec in [Vips.Precision.INTEGER, Vips.Precision.FLOAT]:
                    convolved = im.conv(msk, precision = prec)

                    result = convolved.getpoint(25, 50)
                    true = conv(im, msk, 24, 49)
                    self.assertAlmostEqualObjects(result, true)

                    result = convolved.getpoint(50, 50)
                    true = conv(im, msk, 49, 49)
                    self.assertAlmostEqualObjects(result, true)



if __name__ == '__main__':
    unittest.main()