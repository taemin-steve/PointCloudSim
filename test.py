from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import loadPrcFileData
from panda3d.core import Shader
from draw_sphere import draw_sphere
import panda3d.core as p3d
from point_cloud import draw_pointCloud
import numpy as np

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        vertices = np.random.randn(300000, 3).astype(np.float32)
        colors = np.random.uniform(0.0, 1.0, size=(300000, 3)).astype(np.float32) # 무작위 색상
        draw_pointCloud(self, vertices, colors)
        
        ############################### 위쪽 부분은 point cloud 를 생성하기 위한 파트.#########################
        
        # 카메라 위치 조정 
        self.cam.setPos(0, -40, 0)
        
        #보트 로드
        self.boat = self.loader.loadModel("avikus_boat.glb")
        self.boat.setPos(0,0,1.05)
        self.boat.reparentTo(self.render)
        
        
        #쉐이더 설정 
        my_shader = Shader.load(Shader.SL_GLSL,
                                vertex="shaders/texturing-vert.glsl",
                                fragment="shaders/texturing-frag.glsl")

        self.plane = self.loader.loadModel("models/cam_front")
        self.plane.reparentTo(self.render)
        self.plane.setShader(my_shader)
        self.plane.setPos(-1,0,0)
        self.plane.set_hpr(90, -90, 0)
        
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        vertices = np.random.randn(300000, 3).astype(np.float32)
        colors = np.random.uniform(0.0, 1.0, size=(300000, 3)).astype(np.float32) # 무작위 색상
        draw_pointCloud(self, vertices, colors)
        return Task.cont


app = MyApp()
app.run()