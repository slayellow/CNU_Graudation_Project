import numpy as np
import cv2
import math


class LaneDetection(object):
    def __init__(self):
        pass

    def region_of_interest(self, img, vertices):
        mask = np.zeros_like(img)
        match_mask_color = 255
        cv2.fillPoly(mask, vertices, match_mask_color)
        masked_image = cv2.bitwise_and(img, mask)
        return masked_image


    def draw_lines(self, img, lines, color=[0, 0, 255], thickness=3):
        line_img = np.zeros(
            (
                img.shape[0],
                img.shape[1],
                3
            ),
            dtype=np.uint8
        )
        img = np.copy(img)
        if lines is None:
            return
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_img, (x1, y1), (x2, y2), color, thickness)
        img = cv2.addWeighted(img, 0.8, line_img, 1.0, 0.0)
        return img


    def pipeline(self, image, temp_line):
        return_lines = []
        height = image.shape[0]
        width = image.shape[1]
        # RoI 삼각형
        region_of_interest_vertices = [
            (0, height*7/8),
            (width / 2, height / 2),
            (width, height*7/8),
        ]
        # RoI 사각형
        '''
        region_of_interest_vertices = [
            (0, height*7/8),
            (width/2 - width/8, height/2 + height/8),
            (width/2 + width/8, height/2 + height/8),
            (width, height*7/8)
        ]
        '''
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        cannyed_image = cv2.Canny(gray_image, 100, 200)
        cropped_image = self.region_of_interest(
            cannyed_image,
            np.array(
                [region_of_interest_vertices],
                np.int32
            ),
        )
        lines = cv2.HoughLinesP(
            cropped_image,
            rho=6,
            theta=np.pi / 60,
            threshold=160,
            lines=np.array([]),
            minLineLength=40,
            maxLineGap=25
        )

        left_line_x = []
        left_line_y = []
        right_line_x = []
        right_line_y = []
        try:
            for line in lines:
                for x1, y1, x2, y2 in line:
                    slope = (y2 - y1) / (x2 - x1)
                    if math.fabs(slope) < 0.5:
                        continue
                    if slope <= 0:
                        left_line_x.extend([x1, x2])
                        left_line_y.extend([y1, y2])
                    else:
                        right_line_x.extend([x1, x2])
                        right_line_y.extend([y1, y2])
            min_y = int(image.shape[0] * (3 / 5))
            max_y = int(image.shape[0])
            poly_left = np.poly1d(np.polyfit(
                left_line_y,
                left_line_x,
                deg=1
            ))
            left_x_start = int(poly_left(max_y))
            left_x_end = int(poly_left(min_y))

            poly_right = np.poly1d(np.polyfit(
                right_line_y,
                right_line_x,
                deg=1
            ))
            right_x_start = int(poly_right(max_y))
            right_x_end = int(poly_right(min_y))
            return_lines = [
                    [left_x_start, max_y, left_x_end, min_y],
                    [right_x_start, max_y, right_x_end, min_y],
                ]
            line_image = self.draw_lines(
                image,
                [return_lines],
                thickness=5,
            )
        except TypeError:
            line_image = self.draw_lines(
                image,
                [temp_line],
                thickness=5,
            )
            return line_image, return_lines
        return line_image, return_lines

