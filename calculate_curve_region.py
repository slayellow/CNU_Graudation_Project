import math
import cv2
from sympy import Symbol, solve


class CalculateCurveRegion(object):

    # 직선의 방정식 : fx = (y2-y1)/(x2-x1) * x + (y1 - ((y2-y1)/(x2-x1)*x1))
    # 곡선의 방정식 : fx = ( (x-x2)*(x-x3) ) / ( (x1-x2)*(x1-x3)) * y1 + ( (x-x1)*(x-x3) ) / ( (x2-x1)*(x2-x3)) * y2 + ( (x-x1)*(x-x2) ) / ( (x3-x1)*(x3-x2)) * y3

    def __init__(self):
        self.cnt = 0
        self.cnt1 = 0
        self.Warning = False
        pass

    def calculate_region_video(self, image, bounding_box, lines):  ##
        '''
        겹치는 영역 판단하여 겹치는 부분있으면 퍼센테이지 확인하여 위험 탐지 알림
        :param bounding_box: box list
        :param lines: 2개의 라인 선 list
        :return: image
        '''
        height, width, _ = image.shape
        leftx1, lefty1, leftx2, lefty2, leftx3, lefty3 = lines[0]  # 왼쪽 선 좌표
        rightx1, righty1, rightx2, righty2, rightx3, righty3 = lines[1]  # 오른쪽 선 좌표
        all = height * width
        for box in bounding_box:
            left, right, top, bottom = box  # bounding box 좌표
            bol_area = self.calculate_boundingbox(all, box)
            if bol_area == True:
                find_left = self.calculate_leftline(leftx1, lefty1, leftx2, lefty2, leftx3, lefty3,
                                                    box)  # 왼쪽 선에 겹치는지 확인
                print("왼쪽선 중첩 ? : " + str(find_left))
                if find_left == True:  # 왼쪽 선에 겹치면 도형 판단하여 도형 넓이 계산
                    polygon = self.decide_leftpolygon(leftx1, lefty1, leftx2, lefty2, leftx3, lefty3, box)
                    print("Polygon(triangle - 1, rectangle1 - 2, rectangle2 - 3, pentagon - 4) : " + str(polygon))
                    if polygon == 1:
                        result = self.calculate_lefttriangle(leftx1, lefty1, leftx2, lefty2, leftx3, lefty3, box)
                    elif polygon == 2:
                        result = self.calculate_leftrectangle(leftx1, lefty1, leftx2, lefty2, leftx3, lefty3, box)
                    elif polygon == 3:
                        result = self.calculate_leftrectangle2(leftx1, lefty1, leftx2, lefty2, leftx3, lefty3, box)
                    elif polygon == 4:
                        result = self.calculate_leftpentagon(leftx1, lefty1, leftx2, lefty2, leftx3, lefty3, box)
                else:
                    find_right = self.calculate_rightline(rightx1, righty1, rightx2, righty2, rightx3, righty3,
                                                          box)  # 오른쪽 선에 겹치는지 확인
                    print('오른쪽선 중첩? : ' + str(find_right))
                    if find_right == True:  # 오른쪽 선에 겹치면 도형 판단하여 도형 넓이 계산
                        polygon = self.decide_rightpolygon(rightx1, righty1, rightx2, righty2, rightx3, righty3, box)
                        if polygon == 1:
                            result = self.calculate_righttriangle(rightx1, righty1, rightx2, righty2, rightx3, righty3,
                                                                  box)
                        elif polygon == 2:
                            result = self.calculate_rightrectangle(rightx1, righty1, rightx2, righty2, rightx3, righty3,
                                                                   box)
                        elif polygon == 3:
                            result = self.calculate_rightrectangle2(rightx1, righty1, rightx2, righty2, rightx3,
                                                                    righty3, box)
                        elif polygon == 4:
                            result = self.calculate_rightpentagon(rightx1, righty1, rightx2, righty2, rightx3, righty3,
                                                                  box)
                    else:  # 둘 다 아니면 다음 box 검사
                        continue
                rectangle = abs((right - left)) * abs((bottom - top))  # box 사각형 넓이
                percentage = result / rectangle * 100  # box 대비 중첩된 영역 비율
                print("중첩 영역의 넓이 : " + str(result))
                print("Bounding box의 넓이 : " + str(rectangle))
                print("중첩 비율 : " + str(percentage))
                if percentage >= 20 and percentage < 60:
                    image = self.change_image(image)
                    str = '---------------Warning------------------'
                    break
                else:
                    str = '--------------- No Warning -------------'
            else:
                continue
        return str, image

    def calculate_boundingbox(self, all, bounding_box):
        left, right, top, bottom = bounding_box
        area = (right - left) * (bottom - top)
        print(str(bounding_box) + ", Area : " + str(area))
        percentage = area / all * 100
        print("Box Percentage : " + str(percentage))
        if percentage > 50:
            return False
        else:
            if area > 30000:
                return True
            else:
                return False

    def calculate_leftline(self, x1, y1, x2, y2, x3, y3, box):  ##
        '''
        bounding box가 왼쪽 선에 겹치는지 여부 확인
        :param x1: left 밑 x 좌표
        :param y1: left 밑 y 좌표
        :param x2: left 위 x 좌표
        :param y2: left 위 y 좌표
        :param box: bounding box 좌표
        :return: 겹치면 True, 안 겹치면 False
        '''
        left, right, top, bottom = box
        quadleft = ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3
        quadright = ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / ((x3 - x1) * (x3 - x2)) * y3

        if quadleft >= top:
            if quadright <= bottom and quadleft >= bottom:
                if quadright >= top:  # 삼각형
                    return True
                elif quadright <= top:  # 삼각형 같은 사각형
                    return True
            elif quadright <= bottom and quadleft <= bottom:
                if quadright >= top:  # 오각형 같은 사각형
                    return True
                elif quadright <= top:  # 오각형
                    return True
        else:
            return False

    def calculate_rightline(self, x1, y1, x2, y2, x3, y3, box):  ##
        '''
        bounding box가 오른쪽 선에 겹치는지 여부 확인
        :param x1: right 밑 x 좌표
        :param y1: right 밑 y 좌표
        :param x2: right 위 x 좌표
        :param y2: right 위 y 좌표
        :param box: bounding box 좌표
        :return: 겹치면 True, 안 겹치면 False
        '''
        left, right, top, bottom = box
        quadleft = ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3
        quadright = ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / ((x3 - x1) * (x3 - x2)) * y3

        if quadright >= top:
            if quadleft <= bottom and quadright >= bottom:
                if quadleft >= top:  # 삼각형
                    return True
                elif quadleft <= top:  # 삼각형 같은 사각형
                    return True
            elif quadleft <= bottom and quadright <= bottom:
                if quadleft >= top:  # 오각형 같은 사각형
                    return True
                elif quadleft <= top:  # 오각형
                    return True
        else:
            return False

    def decide_leftpolygon(self, x1, y1, x2, y2, x3, y3, box):  ##
        '''
        왼쪽 겹치는 영역이 삼각형, 사각형, 오각형인지 판단
        :param x1: left 밑 x 좌표
        :param y1: left 밑 y 좌표
        :param x2: left 위 x 좌표
        :param y2: left 위 y 좌표
        :param box: bounding box 좌표
        :return: 삼각형이면 1, 사각형이면 2, 오각형이면 3
        '''
        left, right, top, bottom = box
        quadleft = ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3
        quadright = ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / ((x3 - x1) * (x3 - x2)) * y3

        if quadright <= bottom and quadleft >= bottom:
            if quadright >= top:  # 삼각형
                return 1
            elif quadright <= top:  # 삼각형 같은 사각형
                return 2
        elif quadright <= bottom and quadleft <= bottom:
            if quadright >= top:  # 오각형 같은 사각형
                return 3
            elif quadright <= top:  # 오각형
                return 4

    def decide_rightpolygon(self, x1, y1, x2, y2, x3, y3, box):  ##
        '''
        오른쪽 겹치는 영역이 삼각형, 사각형, 오각형인지 판단
        :param x1: right 밑 x 좌표
        :param y1: right 밑 y 좌표
        :param x2: right 위 x 좌표
        :param y2: right 위 y 좌표
        :param box: bounding box 좌표
        :return: 삼각형이면 1, 사각형이면 2, 오각형이면 3
        '''
        left, right, top, bottom = box
        quadleft = ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3
        quadright = ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / ((x3 - x1) * (x3 - x2)) * y3

        if quadleft <= bottom and quadright >= bottom:
            if quadleft >= top:  # 삼각형
                return 1
            elif quadleft <= top:  # 삼각형 같은 사각형
                return 2
        elif quadleft <= bottom and quadright <= bottom:
            if quadleft >= top:  # 오각형 같은 사각형
                return 3
            elif quadleft <= top:  # 오각형
                return 4

    def calculate_lefttriangle(self, x1, y1, x2, y2, x3, y3, box):
        left, right, top, bottom = box

        # 이차방정식을 풀기 위함
        x = Symbol('x')
        equation = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - bottom
        bottom_x = solve(equation)
        if (left < bottom_x[0] and bottom_x[0] < right):
            del bottom_x[1]
        else:
            del bottom_x[0]

        right_bottom = [right, bottom]
        right_top = [right,
                     ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                                 (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / (
                                 (x3 - x1) * (x3 - x2)) * y3]
        left_bottom = [bottom_x[0], bottom]
        lowerbase = math.sqrt(((left_bottom[1] - right_bottom[1]) * (left_bottom[1] - right_bottom[1])) + (
                    (left_bottom[0] - right_bottom[0]) * (left_bottom[0] - right_bottom[0])))
        height = math.sqrt(((right_top[1] - right_bottom[1]) * (right_top[1] - right_bottom[1])) + (
                    (right_top[0] - right_bottom[0]) * (right_top[0] - right_bottom[0])))
        return (lowerbase * height / 2)

    def calculate_leftrectangle(self, x1, y1, x2, y2, x3, y3, box):  # 삼각형 같은 사각형

        left, right, top, bottom = box

        # 이차방정식을 풀기 위함
        x = Symbol('x')
        equation = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - bottom
        bottom_x = solve(equation)
        if (left < bottom_x[0] and bottom_x[0] < right):
            del bottom_x[1]
        else:
            del bottom_x[0]

        equation1 = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - top
        top_x = solve(equation1)
        if (left < top_x[0] and top_x[0] < right):
            del top_x[1]
        else:
            del top_x[0]

        right_bottom = [right, bottom]
        right_top = [right, top]
        left_bottom = [bottom_x[0], bottom]
        left_top = [top_x[0], top]

        lowerbase = math.sqrt(((left_bottom[1] - right_bottom[1]) * (left_bottom[1] - right_bottom[1])) + (
                    (left_bottom[0] - right_bottom[0]) * (left_bottom[0] - right_bottom[0])))
        upperbase = math.sqrt(((left_top[1] - right_top[1]) * (left_top[1] - right_top[1])) + (
                    (left_top[0] - right_top[0]) * (left_top[0] - right_top[0])))
        height = math.sqrt(((right_top[1] - right_bottom[1]) * (right_top[1] - right_bottom[1])) + (
                    (right_top[0] - right_bottom[0]) * (right_top[0] - right_bottom[0])))
        return (lowerbase + upperbase) * height / 2

    def calculate_leftrectangle2(self, x1, y1, x2, y2, x3, y3, box):

        left, right, top, bottom = box

        right_bottom = [right, bottom]
        right_top = [right,
                     ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                                 (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / (
                                 (x3 - x1) * (x3 - x2)) * y3]
        left_bottom = [left, bottom]
        left_top = [left, ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3]

        lowerbase = math.sqrt(((left_bottom[1] - right_bottom[1]) * (left_bottom[1] - right_bottom[1])) + (
                (left_bottom[0] - right_bottom[0]) * (left_bottom[0] - right_bottom[0])))
        upperbase = math.sqrt(((left_top[1] - right_top[1]) * (left_top[1] - right_top[1])) + (
                (left_top[0] - right_top[0]) * (left_top[0] - right_top[0])))
        height = math.sqrt(((right_top[1] - right_bottom[1]) * (right_top[1] - right_bottom[1])) + (
                (right_top[0] - right_bottom[0]) * (right_top[0] - right_bottom[0])))
        return (lowerbase + upperbase) * height / 2

    def calculate_leftpentagon(self, x1, y1, x2, y2, x3, y3, box):
        left, right, top, bottom = box

        # 이차방정식을 풀기 위함
        x = Symbol('x')
        equation1 = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - top
        top_x = solve(equation1)
        if (left < top_x[0] and top_x[0] < right):
            del top_x[1]
        else:
            del top_x[0]

        left_top = [left, top]
        line_top = [top_x[0], top]
        line_left = [left, ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3]

        lowerbase = math.sqrt(((left_top[1] - line_top[1]) * (left_top[1] - line_top[1])) + (
                (left_top[0] - line_top[0]) * (left_top[0] - line_top[0])))
        height = math.sqrt(((left_top[1] - line_left[1]) * (left_top[1] - line_left[1])) + (
                (left_top[0] - line_left[0]) * (left_top[0] - line_left[0])))

        rec_area = (bottom - top) * (right - left)
        tri_area = lowerbase * height / 2

        return rec_area - tri_area

    def calculate_righttriangle(self, x1, y1, x2, y2, x3, y3, box):
        left, right, top, bottom = box

        # 이차방정식을 풀기 위함
        x = Symbol('x')
        equation = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - bottom
        bottom_x = solve(equation)
        if (left < bottom_x[0] and bottom_x[0] < right):
            del bottom_x[1]
        else:
            del bottom_x[0]

        left_bottom = [left, bottom]
        line_bottom = [bottom_x[0], bottom]
        line_left = [left, ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3]

        lowerbase = math.sqrt(((left_bottom[1] - line_bottom[1]) * (left_bottom[1] - line_bottom[1])) + (
                    (left_bottom[0] - line_bottom[0]) * (left_bottom[0] - line_bottom[0])))
        height = math.sqrt(((line_left[1] - left_bottom[1]) * (line_left[1] - left_bottom[1])) + (
                    (line_left[0] - left_bottom[0]) * (line_left[0] - left_bottom[0])))
        return (lowerbase * height / 2)

    def calculate_rightrectangle(self, x1, y1, x2, y2, x3, y3, box):  # 삼각형 같은 사각형

        left, right, top, bottom = box

        # 이차방정식을 풀기 위함
        x = Symbol('x')
        equation = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - bottom
        bottom_x = solve(equation)
        if (left < bottom_x[0] and bottom_x[0] < right):
            del bottom_x[1]
        else:
            del bottom_x[0]

        equation1 = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - top
        top_x = solve(equation1)
        if (left < top_x[0] and top_x[0] < right):
            del top_x[1]
        else:
            del top_x[0]

        left_top = [left, top]
        line_top = [top_x[0], top]
        line_bottom = [bottom_x[0], bottom]
        left_bottom = [left, bottom]

        lowerbase = math.sqrt(((left_bottom[1] - line_bottom[1]) * (left_bottom[1] - line_bottom[1])) + (
                    (left_bottom[0] - line_bottom[0]) * (left_bottom[0] - line_bottom[0])))
        upperbase = math.sqrt(((line_top[1] - left_top[1]) * (line_top[1] - left_top[1])) + (
                    (line_top[0] - left_top[0]) * (line_top[0] - left_top[0])))
        height = math.sqrt(((left_top[1] - left_bottom[1]) * (left_top[1] - left_bottom[1])) + (
                    (left_top[0] - left_bottom[0]) * (left_top[0] - left_bottom[0])))
        return (lowerbase + upperbase) * height / 2

    def calculate_rightrectangle2(self, x1, y1, x2, y2, x3, y3, box):

        left, right, top, bottom = box

        right_bottom = [right, bottom]
        right_top = [right,
                     ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                                 (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / (
                                 (x3 - x1) * (x3 - x2)) * y3]
        left_bottom = [left, bottom]
        left_top = [left, ((left - x2) * (left - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((left - x1) * (left - x3)) / (
                    (x2 - x1) * (x2 - x3)) * y2 + ((left - x1) * (left - x2)) / ((x3 - x1) * (x3 - x2)) * y3]

        lowerbase = math.sqrt(((left_bottom[1] - right_bottom[1]) * (left_bottom[1] - right_bottom[1])) + (
                (left_bottom[0] - right_bottom[0]) * (left_bottom[0] - right_bottom[0])))
        upperbase = math.sqrt(((left_top[1] - right_top[1]) * (left_top[1] - right_top[1])) + (
                (left_top[0] - right_top[0]) * (left_top[0] - right_top[0])))
        height = math.sqrt(((right_top[1] - right_bottom[1]) * (right_top[1] - right_bottom[1])) + (
                (right_top[0] - right_bottom[0]) * (right_top[0] - right_bottom[0])))
        return (lowerbase + upperbase) * height / 2

    def calculate_rightpentagon(self, x1, y1, x2, y2, x3, y3, box):
        left, right, top, bottom = box

        # 이차방정식을 풀기 위함
        x = Symbol('x')
        equation1 = ((x - x2) * (x - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((x - x1) * (x - x3)) / (
                (x2 - x1) * (x2 - x3)) * y2 + ((x - x1) * (x - x2)) / ((x3 - x1) * (x3 - x2)) * y3 - top
        top_x = solve(equation1)
        if (left < top_x[0] and top_x[0] < right):
            del top_x[1]
        else:
            del top_x[0]

        right_top = [right, top]
        line_top = [top_x[0], top]
        line_right = [right,
                      ((right - x2) * (right - x3)) / ((x1 - x2) * (x1 - x3)) * y1 + ((right - x1) * (right - x3)) / (
                                  (x2 - x1) * (x2 - x3)) * y2 + ((right - x1) * (right - x2)) / (
                                  (x3 - x1) * (x3 - x2)) * y3]

        lowerbase = math.sqrt(((right_top[1] - line_top[1]) * (right_top[1] - line_top[1])) + (
                (right_top[0] - line_top[0]) * (right_top[0] - line_top[0])))
        height = math.sqrt(((right_top[1] - line_right[1]) * (right_top[1] - line_right[1])) + (
                (right_top[0] - line_right[0]) * (right_top[0] - line_right[0])))

        rec_area = (bottom - top) * (right - left)
        tri_area = lowerbase * height / 2

        return rec_area - tri_area


    def change_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        return image