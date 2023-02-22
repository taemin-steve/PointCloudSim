from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import numpy as np
from panda3d.core import Point3, Material
from panda3d.core import GeomNode
from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomPoints

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        def draw_pointCloud(self, vertices, colors):
            points = [Point3(p[0], p[1], p[2]) for p in vertices]

            # Point cloud 노드 생성
            pointCloudNode = GeomNode("pointCloud")

            # Geom 생성
            vformat = GeomVertexFormat.getV3c4()
            vdata = GeomVertexData('point_data', vformat, Geom.UHStatic)
            vertex = GeomVertexWriter(vdata, 'vertex')
            color = GeomVertexWriter(vdata, 'color')

            for point, inputColor in zip(points, colors):
                vertex.addData3f(point)
                color.addData4f(inputColor[0], inputColor[1], inputColor[2], 1.0)

            prim = GeomPoints(Geom.UHStatic)
            prim.addConsecutiveVertices(0, len(points))

            geom = Geom(vdata)
            geom.addPrimitive(prim)

            pointCloudNode.addGeom(geom)

            # Point cloud 노드에 적용할 머티리얼 생성
            material = Material()
            material.setShininess(1000)

            # Point cloud 노드를 렌더링하기
            nodePath = self.render.attachNewNode(pointCloudNode)
            nodePath.setMaterial(material)

        # 정점 정보 생성
        vertices = np.random.randn(300000, 3).astype(np.float32)
        colors = np.random.uniform(0.0, 1.0, size=(300000, 3)).astype(np.float32) # 무작위 색상
        draw_pointCloud(self, vertices, colors)
        
