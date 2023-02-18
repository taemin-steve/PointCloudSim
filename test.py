from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import BoundingSphere
from panda3d.core import LPoint3
from panda3d.core import CollisionSphere, CollisionNode

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # #load Boat map
        self.boat = self.loader.loadModel("avikus_boat.glb")
        self.boat.reparentTo(self.render)
        
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms aon the model.
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)
        

app = MyApp()
app.run()