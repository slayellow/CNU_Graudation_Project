import math
import cv2


class CalculateRegion(object):

# 직선의 방정식 : fx = (y2-y1)/(x2-x1) * x + (y1 - ((y2-y1)/(x2-x1)*x1))


    def __init__(self):
        pass

    def calculate_region(self, image, bounding_box, lines):
        '''
        겹치는 영역 판단하여 겹치는 부분있으면 퍼센테이지 확인하여 위험 탐지 알림
        :param bounding_box: box list
        :param lines: 2개의 라인 선 list
        :return: image
        '''
        leftx1, lefty1, leftx2, lefty2 = lines[0]   # 왼쪽 선 좌표
        rightx1, righty1, rightx2, righty2 = lines[1]   # 오른쪽 선 좌표
        for box in bounding_box:
            left, right, top, bottom = box  # bounding box 좌표
            find_left = self.calculate_leftline(leftx1, lefty1, leftx2, lefty2, box)    # 왼쪽 선에 겹치는지 확인
            find_right = self.calculate_rightline(rightx1, righty1, rightx2, righty2, box)  # 오른쪽 선에 겹치는지 확인
            print(find_left, find_right)
            if find_left == True:   # 왼쪽 선에 겹치면 도형 판단하여 도형 넓이 계산
                polygon = self.decide_leftpolygon(leftx1, lefty1, leftx2, lefty2, box)
                if polygon == 1:
                    result = self.calculate_lefttriangle(leftx1, lefty1, leftx2, lefty2, box)
                elif polygon == 2:
                    self.calculate_leftrectangle(leftx1, lefty1, leftx2, lefty2, box)
                elif polygon == 3:
                    self.calculate_leftpentagon(leftx1, lefty1, leftx2, lefty2, box)
            elif find_right == True:    # 오른쪽 선에 겹치면 도형 판단하여 도형 넓이 계산
                polygon = self.decide_rightpolygon(rightx1, righty1, rightx2, righty2, box)
                if polygon == 1:
                    self.calculate_rigthtriangle(rightx1, righty1, rightx2, righty2, box)
                elif polygon == 2:
                    self.calculate_rightrectangle(rightx1, righty1, rightx2, righty2, box)
                elif polygon == 3:
                    self.calculate_rightpentagon(rightx1, righty1, rightx2, righty2, box)
            else:   # 둘 다 아니면 다음 box 검사
                continue
            rectangle = abs((right-left)) * abs((bottom-top))   # box 사각형 넓이
            percentage = result / rectangle * 100               # box 대비 중첩된 영역 비율
            if percentage >= 3:
                image = self.change_image(image)
                break
        return image


    def calculate_leftline(self, x1, y1, x2, y2, box):
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
        if ((y2-y1)/(x2-x1) * right + (y1 - ((y2-y1)/(x2-x1)*x1))) <= bottom and ((y2-y1)/(x2-x1) * left + (y1 - ((y2-y1)/(x2-x1)*x1))) >= bottom:
            return True
        else:
            return False

    def calculate_rightline(self, x1, y1, x2, y2, box):
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
        if (y2-y1)/(x2-x1) * left + (y1 - ((y2-y1)/(x2-x1)*x1)) <= bottom and (y2-y1)/(x2-x1) * right + (y1 - ((y2-y1)/(x2-x1)*x1)) >= bottom:
            return True
        else:
            return False

    def decide_leftpolygon(self, x1, y1, x2, y2, box):
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
        if (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1)) >= top and (y2 - y1) / (x2 - x1) * left + (y1 - ((y2 - y1) / (x2 - x1) * x1)) >= bottom:
            return 1
        elif (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1)) <= top and (y2 - y1) / (x2 - x1) * left + (y1 - ((y2 - y1) / (x2 - x1) * x1)) >= bottom:
            return 2
        elif (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1)) <= top and (y2 - y1) / (x2 - x1) * left + (y1 - ((y2 - y1) / (x2 - x1) * x1)) <= bottom:
            return 3

    def decide_rightpolygon(self, x1, y1, x2, y2, box):
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
        if (y2 - y1) / (x2 - x1) * left + (y1 - ((y2 - y1) / (x2 - x1) * x1)) >= top and (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1)) >= bottom:
            return 1
        elif (y2 - y1) / (x2 - x1) * left + (y1 - ((y2 - y1) / (x2 - x1) * x1)) <= top and (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1)) >= bottom:
            return 2
        elif (y2 - y1) / (x2 - x1) * left + (y1 - ((y2 - y1) / (x2 - x1) * x1)) <= top and (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1)) <= bottom:
            return 3

    def calculate_lefttriangle(self, x1, y1, x2, y2, box):
        '''
        왼쪽 삼각형의 넓이를 구하는 함수
        :param x1: left 밑 x 좌표
        :param y1: left 밑 y 좌표
        :param x2: left 위 x 좌표
        :param y2: left 위 y 좌표
        :param box: bounding box 좌표
        :return: 삼각형의 넓이
        '''
        left, right, top, bottom = box
        a = [right, bottom]
        b = [right, (y2 - y1) / (x2 - x1) * right + (y1 - ((y2 - y1) / (x2 - x1) * x1))]
        c = [((bottom - (y1 - ((y2 - y1) / (x2 - x1) * x1))) / ((y2 - y1) / (x2 - x1))), bottom]
        ac = math.sqrt(((c[1]-a[1])*(c[1]-a[1])) + ((c[0]-a[0])*(c[0]-a[0])))
        ab = math.sqrt(((b[1]-a[1])*(b[1]-a[1])) + ((b[0]-a[0])*(b[0]-a[0])))
        return (ac * ab / 2)

    def calculate_leftrectangle(self, x1, y1, x2, y2, box):
        left, right, top, bottom = box

    def calculate_leftpentagon(self, x1, y1, x2, y2, box):
        left, right, top, bottom = box

    def calculate_righttriangle(self, x1, y1, x2, y2, box):
        left, right, top, bottom = box

    def calculate_rightrectangle(self, x1, y1, x2, y2, box):
        left, right, top, bottom = box

    def calculate_rightpentagon(self, x1, y1, x2, y2, box):
        left, right, top, bottom = box

    def change_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        return image