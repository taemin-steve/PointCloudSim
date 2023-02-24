from direct.showbase.ShowBase import ShowBase
import numpy as np
from panda3d.core import *
from panda3d.core import Point3, Material
from panda3d.core import GeomNode
from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomPoints

##############################################################################################################
vertices = np.random.randn(300000, 3).astype(np.float32)
colors = np.random.uniform(0.0, 1.0, size=(300000, 3)).astype(np.float32) # 무작위 색상
print(colors.shape)
points = [Point3(p[0], p[1], p[2]) for p in vertices]
# Point cloud 노드 생성
pointCloudNode = GeomNode("pointCloud")
# Geom 생성
vformat = GeomVertexFormat.getV3c4() #아마도 Vector3, Color4 같은 느낌
vdata = GeomVertexData('point_data', vformat, Geom.UHDynamic) #Geom.UHDynamic 으로 바꾸어 주어야 원하는 대로 수정이 가능한것으로
vertex = GeomVertexWriter(vdata, 'vertex')
color = GeomVertexWriter(vdata, 'color')
for point, inputColor in zip(points, colors):
    vertex.addData3f(point)
    color.addData4f(inputColor[0], inputColor[1], inputColor[2], 1.0)
prim = GeomPoints(Geom.UHDynamic)
prim.addConsecutiveVertices(0, len(points))
geom = Geom(vdata)
geom.addPrimitive(prim)
pointCloudNode.addGeom(geom)
# Point cloud 노드에 적용할 머티리얼 생성
material = Material()
material.setShininess(1000)
        
        
class MyApp(ShowBase):
    
    def __init__(self):
        ShowBase.__init__(self)
        # Point cloud 노드를 렌더링하기
        nodePath = self.render.attachNewNode(pointCloudNode)
        nodePath.setMaterial(material)
        
        self.cam.setPos(0, -40, 0)
        self.accept('escape', self.quit)
        
    def quit(self):
        vertices = np.random.randn(300000, 3).astype(np.float32)
        colors = np.random.uniform(0.0, 1.0, size=(300000, 3)).astype(np.float32) # 무작위 색상
        points = [Point3(p[0], p[1], p[2]) for p in vertices]
        
        vertex.setRow(0) # 0번째 버텍스로 이동
        color.setRow(0) # 0번째 버텍스로 이동
        
        for point, inputColor in zip(points, colors):
            vertex.setData3f(point)
            color.setData4f(inputColor[0], inputColor[1], inputColor[2], 1.0)


app = MyApp()
app.run()
