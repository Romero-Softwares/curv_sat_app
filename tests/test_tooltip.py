import unittest

from tooltip import _position_tooltip


class TooltipPositionTests(unittest.TestCase):
    def test_tooltip_is_positioned_to_the_left_near_the_right_edge(self):
        x, y = _position_tooltip(1870, 500, 34, 32, 280, 40, (0, 0, 1920, 1040))

        self.assertEqual((x, y), (1612, 540))

    def test_tooltip_is_positioned_above_near_the_bottom_edge(self):
        x, y = _position_tooltip(500, 1000, 34, 32, 280, 40, (0, 0, 1920, 1040))

        self.assertEqual((x, y), (512, 952))

    def test_tooltip_position_is_clamped_to_the_work_area(self):
        x, y = _position_tooltip(5, 5, 10, 10, 300, 100, (0, 0, 260, 160))

        self.assertEqual((x, y), (8, 23))
