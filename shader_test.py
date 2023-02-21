import cv2
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import glutInit

# OpenCV 비디오 캡처 객체 생성
cap = cv2.VideoCapture("cam_0.mp4")

# OpenGL 초기화 함수
def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, 640.0, 0.0, 480.0)
    glMatrixMode(GL_MODELVIEW)

# OpenGL 디스플레이 함수
def display():
    # 프레임 읽기
    ret, frame = cap.read()

    # 프레임이 없으면 종료
    if not ret:
        cap.release()
        exit()

    # 프레임을 OpenGL 텍스처로 변환
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, frame.shape[1], frame.shape[0], 0, GL_BGR, GL_UNSIGNED_BYTE, frame)

    # 화면에 렌더링
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex2f(640.0, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex2f(640.0, 480.0)
    glTexCoord2f(0.0, 1.0); glVertex2f(0.0, 480.0)
    glEnd()
    glDisable(GL_TEXTURE_2D)

    glutSwapBuffers()

# OpenGL 윈도우 생성 및 메인 루프 실행
if bool(glutInit):
    glutInit
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(640, 480)
    glutCreateWindow(b"OpenGL Video Player")
    glutDisplayFunc(display)
    init()
    glutMainLoop()