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

    def draw_lines(self, img, lines, color=[0, 0, 255], thickness=2):
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

    def pipeline(self, image, temp_line, log):
        """
        Algorithm Process
        :param image: Video Frame
        :param temp_line: formerly line
        :param log: logger object
        :return: line
        """
        return_lines = []       # 결과 좌표
        height = image.shape[0]
        width = image.shape[1]

        # RoI 사각형
        region_of_interest_vertices = [
            (0, height * 9/10),
            (width / 2 - width / 8, height / 2 + height / 8),
            (width / 2 + width / 8, height / 2 + height / 8),
            (width, height * 9/10)
        ]

        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        cannyed_image = cv2.Canny(gray_image, 100, 200)
        cropped_image = self.region_of_interest(
            cannyed_image,
            np.array(
                [region_of_interest_vertices],
                np.int32
            ),
        )

        '''
        image – 8bit, single-channel binary image, canny edge를 선 적용.
        rho – r 값의 범위 (0 ~ 1 실수)
        theta – 𝜃 값의 범위(0 ~ 180 정수)
        threshold – 만나는 점의 기준, 숫자가 작으면 많은 선이 검출되지만 정확도가 떨어지고, 숫자가 크면 정확도가 올라감.
        minLineLength – 선의 최소 길이. 이 값보다 작으면 reject.
        maxLineGap – 선과 선사이의 최대 허용간격. 이 값보다 작으며 reject.
        '''
        lines = cv2.HoughLinesP(
            cropped_image,
            rho=7,
            theta=np.pi / 150,
            threshold=200,
            lines=np.array([]),
            minLineLength=50,
            maxLineGap=25
        )

        left_line_x = []
        left_line_y = []
        right_line_x = []
        right_line_y = []
        try:
            for line in lines:
                for x1, y1, x2, y2 in line:
                    if x1 == x2:
                        continue
                    slope = (y2 - y1) / (x2 - x1)
                    if math.fabs(slope) < 0.5:
                        continue
                    if slope <= 0:
                        left_line_x.extend([x1, x2])
                        left_line_y.extend([y1, y2])
                    else:
                        right_line_x.extend([x1, x2])
                        right_line_y.extend([y1, y2])
            min_y = int(image.shape[0] * (0.725))
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

            if temp_line:
                leftline, rightline = return_lines[0], return_lines[1]
                templeftline, temprightline = temp_line[0], temp_line[1]
                # 현재프레임에서 얻은 차선좌표
                leftx1, lefty1, leftx2, lefty2 = leftline[0], leftline[1], leftline[2], leftline[3]
                rightx1, righty1, rightx2, righty2 = rightline[0], rightline[1], rightline[2], rightline[3]
                # 이전프레임에서 얻은 차선좌표
                templeftx1, templefty1, templeftx2, templefty2 = templeftline[0], templeftline[1], templeftline[2], \
                                                                 templeftline[3]
                temprightx1, temprighty1, temprightx2, temprighty2 = temprightline[0], templeftline[1], temprightline[2], \
                                                                     temprightline[3]

                if abs(leftx1 - templeftx1) > 80 or abs(leftx2 - templeftx2) > 50:
                    temp_return_left = [templeftx1, templefty1, templeftx2, templefty2]
                else:
                    temp_return_left = [leftx1, lefty1, leftx2, lefty2]

                if abs(rightx1 - temprightx1) > 80 or abs(rightx2 - temprightx2) > 50:
                    temp_return_right = [temprightx1, temprighty1, temprightx2, temprighty2]
                else:
                    temp_return_right = [rightx1, righty1, rightx2, righty2]
                return_lines = [temp_return_left, temp_return_right]
                return return_lines

            else:
                return return_lines
        except TypeError as e:
            return return_lines

