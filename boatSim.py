from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter
from panda3d.core import GeomTriangles, GeomNode
from panda3d.core import Point3
import math
from panda3d.core import Camera
from panda3d.core import LPoint3f
from panda3d.core import NodePath, LPoint3
from panda3d.core import PerspectiveLens, LVector3
import panda3d.core as p3d


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # 구체의 반지름과 분할 수를 정의합니다.
        
        def make_sphere(radius,pos,color):
            subdivisions = 32
            
             # 구체의 정점 데이터를 생성합니다.
            format = GeomVertexFormat.getV3()
            vdata = GeomVertexData('sphere', format, Geom.UHStatic)
            vertex = GeomVertexWriter(vdata, 'vertex')
            for i in range(subdivisions):
                for j in range(subdivisions):
                    theta = (i / subdivisions) * 2 * math.pi
                    phi = (j / subdivisions) * math.pi
                    x = radius * math.sin(phi) * math.cos(theta)
                    y = radius * math.sin(phi) * math.sin(theta)
                    z = radius * math.cos(phi)
                    vertex.addData3f(x, y, z)

            # 구체의 삼각형 데이터를 생성합니다.
            tris = GeomTriangles(Geom.UHStatic)
            for i in range(subdivisions):
                for j in range(subdivisions):
                    a = i * subdivisions + j
                    b = (i + 1) % subdivisions * subdivisions + j
                    c = i * subdivisions + (j + 1) % subdivisions
                    tris.addVertices(a, b, c)
                    tris.closePrimitive()

                    a = (i + 1) % subdivisions * subdivisions + j
                    b = (i + 1) % subdivisions * subdivisions + (j + 1) % subdivisions
                    c = i * subdivisions + (j + 1) % subdivisions
                    tris.addVertices(a, b, c)
                    tris.closePrimitive()

            # 구체의 노드를 생성하고, 삼각형과 정점 데이터를 추가합니다.
            geom = Geom(vdata)
            geom.addPrimitive(tris)
            node = GeomNode('sphere')
            node.addGeom(geom)
            
            # 구체를 렌더링합니다.
            sphere = self.render.attachNewNode(node)
            sphere.set_color(color)
            sphere.setPos(pos)
            sphere.setTwoSided(True)
        
        #구를 직접 생성
        make_sphere(0.1,(0,0,0),(1,0,0,1))
        make_sphere(0.1,(0,0,2),(1,1,0,1))
        make_sphere(0.1,(0,0,4),(1,0,1,1))
        make_sphere(0.1,(0,0,6),(0,0,1,1))
        make_sphere(0.1,(0,0,8),(0,1,0,1))
        
        #보트 로드
        self.boat = self.loader.loadModel("avikus_boat.glb")
        self.boat.reparentTo(self.render)
        
        # self.scene = self.loader.loadModel("models/environment")
        # self.scene.reparentTo(self.render)
        
        # self.scene.setScale(0.25, 0.25, 0.25)
        # self.scene.setPos(-8, 42, 0)
        
        # self.camera.setPos(0, 10, 0)
        # self.camera.lookAt(0, 0, 0)
        
        # 카메라 각각의 좌표계를 설정
        camera_front = p3d.NodePath("ChildNode")
        camera_front.reparent_to(self.render)
        camera_front.setPos(2,2,2)
        camera_front.set_hpr(0, 0, 45)
        self.boat.reparentTo(camera_front)
        
        # 카메라 생성
        # base.disableMouse() # 마우스로 컨트롤을 할 수 있게 설정하는 경우 camera가 default로 이동해버림.
        self.camera.setPos(20,20,20)
        self.camera.lookAt(0,0,0)
        
        shader = Shader.load(Shader.SL_GLSL,
                     vertex="myshader.vert",
                     fragment="myshader.frag")
        model.setShader(shader)

app = MyApp()
app.run()
