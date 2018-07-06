#!/usr/bin/env python3
import sys
import cv2
import numpy as np
import matplotlib.image as mpimg
import glob


def get_calibration_param(image_url):
    images = glob.glob(image_url)
    objp = np.zeros((6*9,3), np.float32)
    objp[:,:2] = np.mgrid[0:9, 0:6].T.reshape(-1,2)
    objpoints = [] # 3d points in real world space
    imgpoints = [] # 2d points in image plane.
    corner = (9, 6)
    for image in images:
        img = mpimg.imread(image)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, corner, None)
        if ret:
            objpoints.append(objp)
            imgpoints.append(corners)
    img_size = (img.shape[1], img.shape[0])
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_size,None,None)
    return mtx, dist

def get_undistortion(distorted_img, mtx, dist):
    undist = cv2.undistort(distorted_img, mtx, dist, None, mtx)
    return undist

def input_calibration_file(path="./calibration.npz"):
    try:
        calibration_param = np.load(path)
        return calibration_param['mtx'], calibration_param['dist']
    except IOError as e:
        print(e)
        raise IOError("Please Set Correct Calibration File")

def get_s_binary(undist_img, thres=(110, 255)):
    hls = cv2.cvtColor(undist_img, cv2.COLOR_RGB2HLS)
    h = hls[:, :, 0]
    s = hls[:, :, 2]
    s_binary = np.zeros_like(s)
    s_binary[((s >= thres[0]) & (s <= thres[1])) & (h <= 30)] = 1 #30
    s_binary = gaussian_blur(s_binary, kernel_size=21)#9
    return s_binary

def gaussian_blur(img, kernel_size):
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def adjust_gamma(image, gamma=1.0):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def dir_threshold(img_ch, sobel_kernel=3, thresh=(0, np.pi/2)):
    sobelx = np.absolute(cv2.Sobel(img_ch, cv2.CV_64F, 1, 0, ksize=sobel_kernel))
    sobely = np.absolute(cv2.Sobel(img_ch, cv2.CV_64F, 0, 1, ksize=sobel_kernel))
    abs_grad_dir = np.absolute(np.arctan(sobely/sobelx))
    dir_binary =  np.zeros_like(abs_grad_dir)
    dir_binary[(abs_grad_dir > thresh[0]) & (abs_grad_dir < thresh[1])] = 1
    return dir_binary

def get_slope(undist_img, orient='x', sobel_kernel=3, thres = (0, 255)):
    undist_img = adjust_gamma(undist_img, 0.2)
    gray = cv2.cvtColor(undist_img, cv2.COLOR_RGB2GRAY)
    if orient == 'x':
        slope = np.absolute(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel))
    elif orient == 'y':
        slope = np.absolute(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel))
    else:
        raise KeyError("select 'x' or 'y'")
    scale_factor = np.max(slope) / 255
    scale_slope = (slope / scale_factor).astype(np.uint8)
    slope_binary = np.zeros_like(scale_slope)
    slope_binary[(scale_slope >= thres[0]) & (scale_slope <= thres[1])] = 1
    #dir_binary = dir_threshold(gray, sobel_kernel=sobel_kernel, thresh=(0.3, 1.8))
    #slope_binary[(dir_binary == 0)] = 0
    slope_binary = gaussian_blur(slope_binary, kernel_size=9) # 5
    return slope_binary

def color_slope_thres_conversion(undist_img):
    s_binary = get_s_binary(undist_img, thres=(150, 255))   # 노랑색, 흰색 차선을 찾는 것
    slope = get_slope(undist_img, orient='x',sobel_kernel=7, thres=(25, 255)) #3, 30    / 흰색선을 가져올수 있다.
    color_binary = np.zeros_like(s_binary)
    color_binary[(s_binary == 1) | (slope == 1)] = 1
    return color_binary

def histogram_thresholding(img, xsteps=20, ysteps=40, window_width=10):

    def get_max_index_of_histogram(histogram, left_boundary, right_boundary, window_width=10):
        index_list = []
        side_histogram = histogram[left_boundary : right_boundary]
        for i in range(len(side_histogram) - window_width):
            index_list.append(np.sum(side_histogram[i : i + window_width]))
        index = np.argmax(index_list) + int(window_width / 2) + left_boundary
        return index

    xstride = img.shape[0] // xsteps
    ystride = img.shape[1] // ysteps
    for xstep in range(xsteps):
        histogram = np.sum(img[xstride*xstep : xstride*(xstep+1), :], axis=0)
        boundary = int(img.shape[1] / 2)
        leftindex = get_max_index_of_histogram(histogram, 0, boundary, window_width=window_width)
        rightindex = get_max_index_of_histogram(histogram, boundary, img.shape[1], window_width=window_width)
        if histogram[leftindex] >= 3:
            img[xstride*xstep : xstride*(xstep+1), : leftindex-ysteps] = 0
            img[xstride*xstep : xstride*(xstep+1), leftindex+ysteps+1 : boundary] = 0
        else:
            img[xstride*xstep : xstride*(xstep+1), : boundary] = 0
        if histogram[rightindex] >= 3:
            img[xstride*xstep : xstride*(xstep+1), boundary :rightindex-ysteps] = 0
            img[xstride*xstep : xstride*(xstep+1), rightindex+ysteps+1 :] = 0
        else:
            img[xstride*xstep : xstride*(xstep+1), boundary : ] = 0
    left_fit_line, left_line_equation = cal_poly(img, 0, boundary)
    right_fit_line, right_line_equation = cal_poly(img, boundary, img.shape[1])
    return img, left_fit_line, right_fit_line, left_line_equation, right_line_equation

def cal_poly(img, left_boundary, right_boundary):
    side_img = img[:, left_boundary: right_boundary]
    index = np.where(side_img == 1)
    yvals = index[0]
    xvals = index[1] + left_boundary
    if xvals.size != 0:
        fit_equation = np.polyfit(yvals, xvals, 2)
        yvals = np.arange(img.shape[0])
        fit_line = fit_equation[0]*yvals**2 + fit_equation[1]*yvals + fit_equation[2]
        return fit_line, fit_equation
    else:
        return 0, np.array([10000., 100., 100.])

def add_lines_to_image(undist_img, new_image):          # 여기서 Line 좌표 가져온다.
    height, width= new_image.shape
    index = np.where(new_image == 1)
    pt = np.vstack((index[1], index[0]))
    pt = np.transpose(pt)
    #cv2.fillConvexPoly(undist_img, pt, (255, 93, 74))      # 영역의 음영채우기
    all_lines = []
    lines = []
    left_line = []
    right_line = []
    undist_img[new_image==1] = [255, 0, 0]      # 선 채우기
    for height ,line in enumerate(new_image):
        for width, j in enumerate(line):
            if j == 1:
                all_lines.append([width,height])
    first_height = int(height/2+height/8)+1
    last_height = height
    middle_height = int((first_height + last_height) / 2)
    first_left, first_right = detect_line(all_lines, first_height)
    middle_left, middle_right = detect_line(all_lines, middle_height)
    last_left, last_right = detect_line(all_lines, last_height)
    left_line.append(first_left)
    left_line.append(middle_left)
    left_line.append(last_left)
    right_line.append(first_right)
    right_line.append(middle_right)
    right_line.append(last_right)
    lines.append(left_line)
    lines.append(right_line)
    return undist_img, lines

def detect_line(lines, height):
    temp = []
    for line in lines:
        if line[1] == height:
            temp.append(line)
    return temp[0], temp[-1]        # 왼쪽선좌표, 오른쪽선 좌표


class Perspective_Transform():
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        self.M = cv2.getPerspectiveTransform(self.src, self.dst)
        self.inverse_M = cv2.getPerspectiveTransform(self.dst, self.src)

    def transform(self, undist):
        return cv2.warpPerspective(undist, self.M, (undist.shape[1], undist.shape[0]))

    def inv_transform(self, undist):
        return cv2.warpPerspective(undist, self.inverse_M, (undist.shape[1], undist.shape[0]))


class Line(object):
    def __init__(self):
        self.detected = False
        self.recent_xfitted = [] # x values of the last n fits of the line
        self.bestx = None # average of x values of the fitted line over the last n iteration
        self.best_fit = None #average of polyminal coefficients over the last n iterations
        self.current_fit = [np.array([False])]
        self.current_x = None
        self.radius_of_curvature = None
        self.line_base_pos = None


class Line_detector(object):
    def __init__(self, calibration_path="./calibration.npz"):
        self.left_line = Line()
        self.right_line = Line()
        self.yvals = np.arange(720)
        self.detected = None
        self.count = 0
        try:
            self.camera_mtx, self.dist_coeff = input_calibration_file(path=calibration_path)
        except IOError as e:
            sys.exit()

    def decide_src_dst(self, width, height):
        # Hard Coding 되어있는 부분 RoI라고 생각하면 된다.
        src = np.array([[width/2-width/8, height/2+height/8], [width/2+width/8, height/2+height/8],
                        [width-40, height], [40, height]], dtype=np.float32)
        dst = np.array([[0, 0], [width, 0],
                        [width-40, height], [40, height]], dtype=np.float32)
        self.bird_view_transformer = Perspective_Transform(src, dst)

    def get_filtered_img_and_cal_poly(self, converted_img, width=30):
        image = self.mask_image_by_average_lines(converted_img, width=width)
        _, self.left_line.current_fit = self.cal_poly(image, 0, int(image.shape[1] / 2))
        _, self.right_line.current_fit = self.cal_poly(image, int(image.shape[1] / 2), image.shape[1])
        return image

    def mask_image_by_average_lines(self, converted_img, width=30):
        image = np.zeros_like(converted_img)
        for yv, ll in zip(self.yvals, self.left_line.bestx):
            image[yv, int(ll-width):int(ll+width)] = converted_img[yv, int(ll-width):int(ll+width)] # modify code
        for yv, rl in zip(self.yvals, self.right_line.bestx):
            image[yv, int(rl-width):int(rl+width)] = converted_img[yv, int(rl-width):int(rl+width)] # modify code
        return image

    def mask_image_by_lines(self, original_image, width=10):
        image = np.zeros_like(original_image)
        for yv, ll in zip(self.yvals, self.left_line.bestx):
            image[yv, int(ll-width):int(ll+width)] = 1              #modify code
        for yv, rl in zip(self.yvals, self.right_line.bestx):
            image[yv, int(rl-width) : int(rl+width)] = 1            #modify code
        return image


    def cal_poly(self, img, left_boundary, right_boundary):
        side_img = img[:, left_boundary: right_boundary].copy()
        index = np.where(side_img == 1)
        yvals = index[0]
        xvals = index[1] + left_boundary
        if xvals.size != 0:
            fit_equation = np.polyfit(yvals, xvals, 2)
            fit_line = fit_equation[0]*self.yvals**2 + fit_equation[1]*self.yvals + fit_equation[2]
            return fit_line, fit_equation
        else:
            return 0, np.array([10000., 100., 100.])

    def check_parallel(self):
        return True if (np.abs(self.left_line.current_fit[0] - self.right_line.current_fit[0]) < 0.01) else False

    def check_similarity(self, side='left'):
        if side == 'left':
            return True if (np.abs(self.left_line.current_fit[0] - self.left_line.best_fit[0]) < 0.0005) else False
        else:
            return True if (np.abs(self.right_line.current_fit[0] - self.right_line.best_fit[0]) < 0.0005) else False

    def check_line(self):
        return self.check_similarity(side='right') and self.check_similarity(side='left') and self.check_parallel()

    def cal_bestx_and_fit(self, weight=0.2):
        self.left_line.best_fit = self.left_line.best_fit * (1 - weight) + self.left_line.current_fit * weight
        self.left_line.bestx = self.left_line.best_fit[0]*self.yvals**2 + self.left_line.best_fit[1]*self.yvals + self.left_line.best_fit[2]
        self.right_line.best_fit = self.right_line.best_fit * (1 - weight) + self.right_line.current_fit * weight
        self.right_line.bestx = self.right_line.best_fit[0]*self.yvals**2 + self.right_line.best_fit[1]*self.yvals + self.right_line.best_fit[2]
        self.count = 0

    def __cal_curvature(self):
        ym_per_pix = 30./720
        xm_per_pix = 3.7/700
        left_fit_cr = np.polyfit(self.yvals * ym_per_pix, self.left_line.bestx * xm_per_pix, 2)
        right_fit_cr = np.polyfit(self.yvals * ym_per_pix, self.right_line.bestx * xm_per_pix, 2)
        self.left_line.radius_of_curvature = ((1 + (2*left_fit_cr[0]*np.max(self.yvals) + left_fit_cr[1])**2)**1.5) \
                                     /np.absolute(2*left_fit_cr[0])
        self.right_line.radius_of_curvature = ((1 + (2*right_fit_cr[0]*np.max(self.yvals) + right_fit_cr[1])**2)**1.5) \
                                        /np.absolute(2*right_fit_cr[0])

    def select_bestx_and_fit(self, image, temp_best_lines):
        best_lines = []
        if self.detected:
            final_bird_view_img = self.get_filtered_img_and_cal_poly(image, width=50)
            if self.check_line():
                self.cal_bestx_and_fit()
            else:
                self.count += 1
                if self.count == 2:
                    self.detected = None
                    self.count = 0
        else:
            final_bird_view_img, left_line, right_line, left_line_equation, right_line_equation = \
                histogram_thresholding(image, xsteps=20, ysteps=25, window_width=15)
            self.left_line.current_fit = left_line_equation
            self.right_line.current_fit = right_line_equation

            if not self.check_parallel():                   # 선을 못딸경우 이전 값 넣는 코드
                self.left_line.bestx = temp_best_lines[0]
                self.left_line.best_fit = temp_best_lines[1]
                self.right_line.bestx = temp_best_lines[2]
                self.right_line.best_fit = temp_best_lines[3]
                self.detected = False
                check = False
            else:
                self.left_line.bestx = left_line
                self.left_line.best_fit = left_line_equation
                self.right_line.bestx = right_line
                self.right_line.best_fit = right_line_equation
                self.detected = True
                best_lines.append(self.left_line.bestx)
                best_lines.append(self.left_line.best_fit)
                best_lines.append(self.right_line.bestx)
                best_lines.append(self.right_line.best_fit)
                check = True
        return final_bird_view_img, best_lines, check

    def process_image(self, distorted_image, temp_best_lines):
        height,width,_ = distorted_image.shape
        self.decide_src_dst(width, height)
        undist_img = get_undistortion(distorted_image, self.camera_mtx, self.dist_coeff)    #왜곡이미지 왜곡없애는이미지로 바꾸기
        bird_view = self.bird_view_transformer.transform(undist_img)        # RoI영역을 설정한다고 생각하면 됨 / Return : Image
        #cv2.imshow("bird_view", bird_view)             # bird view 보는 코드
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        converted_img = color_slope_thres_conversion(bird_view)
        final_bird_view_img, best_lines, line_check= self.select_bestx_and_fit(converted_img, temp_best_lines)  # 여기서 선 지정하고 라인 땃는지 안땃는지 확인
        final_bird_view_img = self.mask_image_by_lines(final_bird_view_img)                              # 선 그림
        new_image = self.bird_view_transformer.inv_transform(final_bird_view_img)
        if line_check:
            undist_img, lines = add_lines_to_image(undist_img, new_image)
            return undist_img, lines, best_lines
        else:
            undist_img, lines = add_lines_to_image(undist_img, new_image)
            return undist_img, [], []



def curve_laneDetection(frame, temp_image):
    camera_matrix, dist_coeff = get_calibration_param('./camera_cal/calibration*.jpg')
    np.savez("./calibration.npz", mtx=camera_matrix, dist=dist_coeff)
    ld = Line_detector()
    frame, lines, new_image = ld.process_image(frame, temp_image)
    return frame, lines, new_image
