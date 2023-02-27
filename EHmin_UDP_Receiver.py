import threading
import socket
import struct

import numpy as np
import cv2 as cv
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Shader
import panda3d.core as p3d
import panda3d

print('Pandas Version :', panda3d.__version__)

############ Main Thread
class SurroundView(ShowBase):
    def __init__(self):
        super().__init__()
        
        # https://docs.panda3d.org/1.10/python/programming/render-attributes/antialiasing
        self.render.setAntialias(p3d.AntialiasAttrib.MAuto)
        # 카메라 위치 조정 
        self.cam.setPos(0, 0, 8000)
        self.cam.lookAt(p3d.LPoint3f(0, 0, 0), p3d.LVector3f(0, 1, 0))
        #self.trackball.node().setMat(self.cam.getMat())
        #self.trackball.node().reset()
        #self.trackball.node().set_pos(0, 30, 0)
        
        #보트 로드
        self.boat = self.loader.loadModel("avikus_boat.glb")
        self.boat.setScale(p3d.Vec3(100, 100, 100))
        bbox = self.boat.getTightBounds()
        print("****************************************")
        print(bbox)
        center = (bbox[0] + bbox[1]) * 0.5
        self.boat.setPos(-center)
        self.boat.set_hpr(0, 90, 90)
        self.boat.reparentTo(self.render)
        
        self.axis = self.loader.loadModel('zup-axis')
        self.axis.setPos(0, 0, 0)
        self.axis.setScale(100)
        self.axis.reparentTo(base.render)
        
        self.isPointCloudSetup = False
        self.lidarRes = 0
        self.lidarChs = 0
        self.numLidars = 0
        def GeneratePlaneNode(svmBase):
            #shader setting for SVM
            svmBase.planeShader = Shader.load(
                Shader.SL_GLSL, vertex="svm_vs.glsl", fragment="svm_ps.glsl")
            vdata = p3d.GeomVertexData(
                'triangle_data', p3d.GeomVertexFormat.getV3t2(), p3d.Geom.UHStatic)
            vdata.setNumRows(4)  # optional for performance enhancement!
            vertex = p3d.GeomVertexWriter(vdata, 'vertex')
            texcoord = p3d.GeomVertexWriter(vdata, 'texcoord')

            bbox = svmBase.boat.getTightBounds()
            print(bbox)
            waterZ = bbox[0].z + (bbox[1].z - bbox[0].z) * 0.2
            waterPlaneLength = 2500
            vertex.addData3(-waterPlaneLength, waterPlaneLength, waterZ)
            vertex.addData3(waterPlaneLength, waterPlaneLength, waterZ)
            vertex.addData3(waterPlaneLength, -waterPlaneLength, waterZ)
            vertex.addData3(-waterPlaneLength, -waterPlaneLength, waterZ)
            texcoord.addData2(0, 0)
            texcoord.addData2(1, 0)
            texcoord.addData2(1, 1)
            texcoord.addData2(0, 1)

            primTris = p3d.GeomTriangles(p3d.Geom.UHStatic)
            primTris.addVertices(0, 1, 2)
            primTris.addVertices(0, 2, 3)

            geom = p3d.Geom(vdata)
            geom.addPrimitive(primTris)
            geomNode = p3d.GeomNode("SVM Plane")
            geomNode.addGeom(geom)
            # note nodePath is the instance for node (obj resource)
            svmBase.plane = p3d.NodePath(geomNode)
            svmBase.plane.setTwoSided(True)
            svmBase.plane.setShader(svmBase.planeShader)
            svmBase.plane.reparentTo(svmBase.render)

        GeneratePlaneNode(self)

mySvm = SurroundView()


#vertices = np.random.uniform(-30.0, 30.0, size=(12800, 3)).astype(np.float32)
#colors = np.random.uniform(0.0, 1.0, size=(12800, 3)).astype(np.float32) # 무작위 색상
#points = [p3d.LPoint3f(p[0], p[1], p[2]) for p in vertices]
#print(len(points))

def GeneratePointNode(task):
    svmBase = mySvm
    if svmBase.lidarRes == 0 or svmBase.lidarChs == 0 or svmBase.numLidars == 0:
        return task.cont

    # note: use Geom.UHDynamic instead of Geom.UHStatic (resource setting for immutable or dynamic)
    vdata = p3d.GeomVertexData(
        'point_data', p3d.GeomVertexFormat.getV3c4(), p3d.Geom.UHDynamic)
    numMaxPoints = svmBase.lidarRes * svmBase.lidarChs * svmBase.numLidars
    # 4 refers to the number of cameras
    vdata.setNumRows(numMaxPoints)
    vertex = p3d.GeomVertexWriter(vdata, 'vertex')
    color = p3d.GeomVertexWriter(vdata, 'color')
    #vertex.reserveNumRows(numMaxPoints)
    #color.reserveNumRows(numMaxPoints)
    vertex.setRow(0)
    color.setRow(0)
    # the following two points define the initial mix/max bounding box used for view-frustom culling
    # as the point cloud is supposed to be visible at all time, the min/max bounding box is set to large enough 
    vertex.addData3f(-1000.0, -1000.0, -1000.0)
    vertex.addData3f(1000.0, 1000.0, 1000.0)
    color.addData4f(0, 0, 0, 0.0)
    color.addData4f(0, 0, 0, 0.0)
    for i in range(numMaxPoints):
        vertex.addData3f(1000.0, 1000.0, 1000.0)
        # https://docs.panda3d.org/1.9/cpp/programming/internal-structures/other-manipulation/more-about-reader-writer-rewriter
        # This allows you to store color components in the range 0.0 .. 1.0, and get the expected result (that is, the value is scaled into the range 0 .. 255). A similar conversion happens when data is read.
        color.addData4f(0, 0, 0, 0.0)

    #vertex.setRow(0)
    #color.setRow(0)
    #for point, inputColor in zip(points, colors):
    #    vertex.addData3f(point)
    #    color.addData4f(inputColor[0], inputColor[1], inputColor[2], 1.0)

    primPoints = p3d.GeomPoints(p3d.Geom.UHDynamic)
    primPoints.addConsecutiveVertices(0, numMaxPoints)
    #primPoints.addConsecutiveVertices(0, len(points))

    geom = p3d.Geom(vdata)
    geom.addPrimitive(primPoints)
    geomNode = p3d.GeomNode("Lidar Points")
    geomNode.addGeom(geom)

    svmBase.pointsVertex = vertex
    svmBase.pointsColor = color
    svmBase.points = p3d.NodePath(geomNode)
    svmBase.points.setTwoSided(True)
    #self.points.setShader(svmBase.planeShader)
    svmBase.points.reparentTo(svmBase.render)

    #material = p3d.Material()
    #material.setShininess(1000)
    #svmBase.points.setMaterial(material)
    svmBase.points.set_render_mode_thickness(5)

    svmBase.isPointCloudSetup = True
    return task.done  # remove this task


####################### UDP Thread

localIP = "127.0.0.1"
localPort = 12000
bufferSize = 60000 

#msgFromServer = "Hello UDP Client"

bytesToSend = b'17'# str.encode(msgFromServer)

# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)


# Bind to address and ip
UDPServerSocket.bind((localIP, localPort))


print("UDP server up and listening")

mySvm.isInitializedUDP = True

color_map = [(128, 64,128),
             (244, 35,232),
             ( 70, 70, 70),
             (102,102,156),
             (190,153,153),
             (153,153,153),
             (250,170, 30),
             (220,220,  0),
             (107,142, 35),
             (152,251,152),
             ( 70,130,180),
             (220, 20, 60),
             (255,  0,  0),
             (  0,  0,142),
             (  0,  0, 70),
             (  0, 60,100),
             (  0, 80,100),
             (  0,  0,230),
             (119, 11, 32)]

def ReceiveData():
    # Listen for incoming datagrams
    while(True):

        #print("listening")
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        #print("got it")
        
        packetInit = bytesAddressPair[0]
        addressInit = bytesAddressPair[1]

        #clientMsg = "Message from Client:{}".format(message)
        clientIP = "Client IP Address:{}".format(addressInit)

        index = int.from_bytes(packetInit[0:4], "little")
        
        if index == 0xffffffff:
            #print("packet start")
            packetNum = int.from_bytes(packetInit[4:8], "little")
            bytesPoints = int.from_bytes(packetInit[8:12], "little")
            bytesDepthmap = int.from_bytes(packetInit[12:16], "little")
            bytesRGBmap = int.from_bytes(packetInit[16:20], "little")
            numLidars = int.from_bytes(packetInit[20:24], "little")
            lidarRes = int.from_bytes(packetInit[24:28], "little")
            lidarChs = int.from_bytes(packetInit[28:32], "little")
            imageWidth = int.from_bytes(packetInit[32:36], "little")
            imageHeight = int.from_bytes(packetInit[36:40], "little")
            
            if packetNum == 0:
                UDPServerSocket.sendto(bytesToSend, addressInit)
                continue
            
            UDPServerSocket.sendto(bytesToSend, addressInit)

            fullPackets = bytearray(b'')
            #fullPackets = bytes(b'')
            packetIndex = 0
            while(packetIndex < packetNum):
                bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
                packet = bytesAddressPair[0]
                address = bytesAddressPair[1]
                UDPServerSocket.sendto(bytesToSend, addressInit)
                index = int.from_bytes(packet[0:4], "little")
                if (index != packetIndex) :
                    print(("Error {id}").format(id = index))
                packetIndex += 1
                fullPackets += packet[4:]
                #print(("index {i}, num bytes {b}").format(i=index, b=len(packet)))
                
            #print(("Bytes of All Packets: {d}").format(d=len(fullPackets)))
            # to do 

            if mySvm.isInitializedUDP == True:
                print(("Num Packets : {Num}").format(Num=packetNum))
                print(("Bytes of Points : {Num}").format(Num=bytesPoints))
                print(("Bytes of RGB map : {Num}").format(Num=bytesRGBmap))
                print(("Bytes of Depth map : {Num}").format(Num=bytesDepthmap))
                print(("Num Lidars : {Num}").format(Num=numLidars))
                print(("Lidar Resolution : {Num}").format(Num=lidarRes))
                print(("Lidar Channels : {Num}").format(Num=lidarChs))
                print(("Camera Width : {Num}").format(Num=imageWidth))
                print(("Camera Height : {Num}").format(Num=imageHeight))
                mySvm.isInitializedUDP = False

                mySvm.lidarRes = lidarRes
                mySvm.lidarChs = lidarChs
                mySvm.numLidars = numLidars
                mySvm.taskMgr.add(GeneratePointNode, "GeneratePointNode")
                
                # Create a 4x4 matrix
                fov = 90.0
                aspectRatio = 1.0
                lens = p3d.PerspectiveLens()
                lens.set_fov(fov)
                lens.set_aspect_ratio(aspectRatio)
                lens.set_near(1.0)
                lens.set_far(10000.0)
                projMat = lens.get_projection_mat()

                sensor_pos_array = [
                    p3d.Vec3(30, 0, 40), 
                    p3d.Vec3(0, 60, 40), 
                    p3d.Vec3(-40, 0, 40), 
                    p3d.Vec3(0, -80, 40)
                    ]
                sensor_rot_z_array = [0, 90, 180, -90]
                cam_pos = p3d.Vec3(0, 0, 50)
                cam_rot_y = -10

                def computeLookAt(camera_pos, camera_target, camera_up) : 
                    forward = camera_target - camera_pos
                    forward.normalize()
                    right = p3d.LVector3f.cross(camera_up, forward)
                    right.normalize()
                    up = p3d.LVector3f.cross(forward, right)
                    return p3d.LMatrix4f(right[0], up[0], forward[0], 0.0,
                        right[1], up[1], forward[1], 0.0,
                        right[2], up[2], forward[2], 0.0,
                        -p3d.LVector3f.dot(right, camera_pos),
                        -p3d.LVector3f.dot(up, camera_pos),
                        -p3d.LVector3f.dot(forward, camera_pos), 1.0)

                localCamMat = computeLookAt(p3d.Vec3(0, 0, 0), p3d.Vec3(1, 0, 0), p3d.Vec3(0, 0, 1))
                camMat = p3d.Mat4.translateMat(cam_pos) * p3d.Mat4.rotateMat(cam_rot_y, p3d.Vec3(0, -1, 0)) * localCamMat
                camMat_array = [p3d.Mat4(localCamMat), p3d.Mat4(localCamMat), p3d.Mat4(localCamMat), p3d.Mat4(localCamMat)]
                sensorMat_array = [p3d.Mat4(), p3d.Mat4(), p3d.Mat4(), p3d.Mat4()]
                imgIdx = 0
                for camMat, sensorMat, deg, pos in zip(camMat_array, sensorMat_array, sensor_rot_z_array, sensor_pos_array):
                    sensorMat = p3d.Mat4.translateMat(pos.x, -pos.y, pos.z) * p3d.Mat4.rotateMat(deg, p3d.Vec3(0, 0, 1))
                    sensorMat_array[imgIdx] = sensorMat
                    camMat = sensorMat * camMat
                    mySvm.plane.setShaderInput("world2image" + str(imgIdx), projMat * camMat)
                    imgIdx += 1

                #mySvm.planePnm = p3d.PNMImage()
                mySvm.planeTexs = [p3d.Texture(), p3d.Texture(), p3d.Texture(), p3d.Texture()]
                for i in range(4):
                    mySvm.planeTexs[i].setup2dTexture(
                        imageWidth, imageHeight, p3d.Texture.T_unsigned_byte, p3d.Texture.F_rgba)
                    mySvm.plane.setShaderInput(
                        'myTexture' + str(i), mySvm.planeTexs[i])
                
                mySvm.semanticTexs = [p3d.Texture(), p3d.Texture(), p3d.Texture(), p3d.Texture()]
                for i in range(4):
                    mySvm.semanticTexs[i].setup2dTexture(
                        imageWidth, imageHeight, p3d.Texture.T_unsigned_byte, p3d.Texture.F_red)
                    mySvm.plane.setShaderInput(
                        'semanticTex' + str(i), mySvm.semanticTexs[i])

                mySvm.sensorMat_array = sensorMat_array
                print("Texture Initialized!")
                
            if mySvm.isPointCloudSetup == True:
                #print("Point Clout Update!!")
                # point cloud buffer : fullPackets[0:bytesPoints]
                numMaxPoints = lidarRes * lidarChs * numLidars
                numProcessPoints = 0
                
                mySvm.pointsVertex.setRow(0)
                mySvm.pointsColor.setRow(0)
                offsetPoints = 0
                for i in range(4):
                    numSingleLidarPoints = int.from_bytes(fullPackets[offsetPoints: 4 + offsetPoints], "little")
                    #print(("Num Process Points : {Num}").format(Num=numSingleLidarPoints))

                    matSensor = mySvm.sensorMat_array[i] 
                    offsetPoints += 4
                    numProcessPoints += numSingleLidarPoints
                    for j in range(numSingleLidarPoints):
                        pX = struct.unpack('<f', fullPackets[0 + offsetPoints : 4 + offsetPoints])[0]
                        pY = struct.unpack('<f', fullPackets[4 + offsetPoints : 8 + offsetPoints])[0]
                        pZ = struct.unpack('<f', fullPackets[8 + offsetPoints: 12 + offsetPoints])[0]
                        #cR = np.frombuffer(fullPackets[12 + offsetPoints, 13 + offsetPoints], dtype=np.int8)[0]
                        cR = int.from_bytes(fullPackets[12 + offsetPoints : 13 + offsetPoints], "little")
                        cG = int.from_bytes(fullPackets[13 + offsetPoints : 14 + offsetPoints], "little")
                        cB = int.from_bytes(fullPackets[14 + offsetPoints : 15 + offsetPoints], "little")
                        cA = int.from_bytes(fullPackets[15 + offsetPoints : 16 + offsetPoints], "little")
                        #if j == 17 :
                        #    print(("pos : {}, {}, {}, {}, {}").format(i, offsetPoints, pX, pY, pZ))
                        #    print(("clr : {}, {}, {}, {}, {}, {}").format(i, offsetPoints, cR, cG, cB, cA))
                        offsetPoints += 16
                        posPoint = p3d.LPoint3f(pX, pY, pZ)
                        # to do : transform posPoint (local) to world
                        posPointWS = matSensor.xformPoint(posPoint)
                        posPointWS.y *= -1
                        #if j == 0 : 
                        #    print(matSensor)
                        mySvm.pointsVertex.setData3f(posPointWS)
                        mySvm.pointsColor.setData4f(cB / 255.0, cG / 255.0, cR / 255.0, cA / 255.0)
                        # if i == 0:
                        #     mySvm.pointsColor.setData4f(0, 0, 1, 1)
                        # elif i == 1:
                        #     mySvm.pointsColor.setData4f(0, 1, 0, 1)
                        # elif i == 2:
                        #     mySvm.pointsColor.setData4f(1, 0, 0, 1)
                        # elif i == 3:
                        #     mySvm.pointsColor.setData4f(0, 1, 1, 1)



                        #mySvm.pointsColor.setData4f(1.0, 0, 0, 1.0)
                    #print(("Num Process Points : {Num}").format(Num=numProcessPoints))

                for i in range(numMaxPoints - numProcessPoints):
                    mySvm.pointsVertex.setData3f(10000, 10000, 10000)
                    mySvm.pointsColor.setData4f(0, 0, 0, 0)
                    
                #mySvm.pointsVertex.setRow(0)
                #mySvm.pointsColor.setRow(0)
                #for point, inputColor in zip(points, colors):
                #    mySvm.pointsVertex.addData3f(point)
                #    mySvm.pointsColor.addData4f(inputColor[0], inputColor[1], inputColor[2], 1.0)
                #print(("Total Points : {Num}").format(Num=numProcessPoints))
                #print(("Remaining Points : {Num}").format(Num=numMaxPoints - numProcessPoints))

                #print(("Is Position End : {End}").format(End=mySvm.pointsVertex.isAtEnd()))
                #print(("Is Color End : {End}").format(End=mySvm.pointsColor.isAtEnd()))
                    
            # depth buffer : fullPackets[bytesPoints:bytesPoints + bytesDepthmap] ... 4 of (lidarRes * lidarchs * 4 bytes) 

            offsetColor = bytesPoints + bytesDepthmap
            imgBytes = imageWidth * imageHeight * 4
            imgs = []
            semantics = []
            for i in range(8):
                #print(("AAA-1 {aa}, {bb}, {cc}").format(aa=imgBytes, bb=offsetColor, cc=i))
                imgnp = np.array(
                    fullPackets[offsetColor + imgBytes * i: offsetColor + imgBytes * (i + 1)], dtype=np.uint8)

                #print("AAA-2")
                img = imgnp.reshape((imageWidth, imageHeight, 4))

                #print("AAA-3")
                if i % 2 == 0:  # imgs
                    imgs.append(img)
                    #print("AAA-4")
                    # https://docs.panda3d.org/1.10/python/programming/texturing/simple-texturing
                    # https://docs.panda3d.org/1.10/cpp/programming/advanced-loading/loading-resources-from-memory
                    mySvm.planeTexs[int(i / 2)].setRamImage(img)
                    #print(("Plane Texture : {Num}").format(Num=i))
                else:  # semantics
                    semantic = np.zeros_like(img).astype(np.uint8)
                    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
                    for j, color in enumerate(color_map):
                        for k in range(3):
                            semantic[:, :, k][img[:, :] == j] = color[k]
                    semantics.append(semantic)
                    mySvm.semanticTexs[int(i / 2)].setRamImage(img)


            # cv.imshow('image_deirvlon 0', imgs[0])
            # cv.imshow('image_deirvlon 1', imgs[1])
            # cv.imshow('image_deirvlon 2', imgs[2])
            # cv.imshow('image_deirvlon 3', imgs[3])
            # cv.imshow("semantic_deirvlon 0", semantics[0])
            # cv.imshow("semantic_deirvlon 1", semantics[1])
            # cv.imshow("semantic_deirvlon 2", semantics[2])
            # cv.imshow("semantic_deirvlon 3", semantics[3])
            # cv.waitKey(1)
            

    #print(("Packets : {p0}, {p1}, {p2}, {p3}").format(p0=packet[0], p1=packet[1], p2=packet[2], p3=packet[3]))
    #print(index)
    #print(clientIP)

    # Sending a reply to client

if __name__ == "__main__":
    t = threading.Thread(target=ReceiveData, args=())
    t.start()

    print("SVM Start!")
    mySvm.run()