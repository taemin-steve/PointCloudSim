import threading
import socket
import struct
import numpy as np
import cv2 as cv
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from panda3d.core import Shader
import panda3d.core as p3d
import panda3d
from panda3d.core import *
from panda3d.core import Point3, Material
from panda3d.core import GeomNode
from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomPoints

vertices = np.random.randn(5000, 3).astype(np.float32)
colors = np.random.uniform(0.0, 1.0, size=(5000, 3)).astype(np.float32) # 무작위 색상
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

print('Pandas Version :', panda3d.__version__)

############ Main Thread
class SurroundView(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # Point cloud 노드를 렌더링하기
        nodePath = self.render.attachNewNode(pointCloudNode)
        nodePath.setMaterial(material)
        
        self.cam.setPos(0, -40, 0)
        # self.accept('escape', self.quit)

mySvm = SurroundView()

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

def ReceiveData():
    # Listen for incoming datagrams
    while(True):

        print("listening")
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        print("got it")
        
        packetInit = bytesAddressPair[0]
        addressInit = bytesAddressPair[1]

        #clientMsg = "Message from Client:{}".format(message)
        clientIP = "Client IP Address:{}".format(addressInit)

        index = int.from_bytes(packetInit[0:4], "little")
        
        if index == 0xffffffff:
            print("packet start")
            packetNum = int.from_bytes(packetInit[4:8], "little")
            bytesPoints = int.from_bytes(packetInit[8:12], "little")
            bytesDepthmap = int.from_bytes(packetInit[12:16], "little")
            bytesRGBmap = int.from_bytes(packetInit[16:20], "little")
            print(("Num Packets : {Num}").format(Num=packetNum))
            print(("Bytes of Points : {Num}").format(Num=bytesPoints))
            print(("Bytes of RGB map : {Num}").format(Num=bytesRGBmap))
            print(("Bytes of Depth map : {Num}").format(Num=bytesDepthmap))
            
            if packetNum == 0:
                UDPServerSocket.sendto(bytesToSend, addressInit)
                continue
            
            UDPServerSocket.sendto(bytesToSend, addressInit)

            fullPackets = bytearray(b'')
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
                
            # print(("Bytes of All Packets: {d}").format(d=len(fullPackets)))
            # # to do 
            # lidarRes = 100
            # lidarchs = 32
            # imageWidth = 256
            # imageHeight = 256

            pc_position = []
            pc_color = []
            for i in range(0,len(fullPackets[0:bytesPoints]),16):
                pc_position.append([struct.unpack('f',fullPackets[i:i+4]), struct.unpack('f',fullPackets[i+4:i+8]),struct.unpack('f',fullPackets[i+8:i+12])])
                pc_color.append([fullPackets[i + 12],fullPackets[i +13],fullPackets[i +14],fullPackets[i +15]])

            pc_position = np.array(pc_position )
            pc_position = pc_position .reshape(-1,3)
            pc_color = np.array(pc_color)
            print(pc_color.shape)

            pc_position = [Point3(p[0], p[1], p[2]) for p in pc_position]
        
            vertex.setRow(0) # 0번째 버텍스로 이동
            color.setRow(0) # 0번째 버텍스로 이동

            for point, inputColor in zip(pc_position, pc_color):
                vertex.setData3f(point)
                color.setData4f(inputColor[0]/255, inputColor[1]/255, inputColor[2]/255, 1.0)

            # point cloud buffer : fullPackets[0:bytesPoints]
            # depth buffer : fullPackets[bytesPoints:bytesPoints + bytesDepthmap] ... 4 of (lidarRes * lidarchs * 4 bytes) 

            # offsetColor = bytesPoints + bytesDepthmap
            # imgBytes = imageWidth * imageHeight * 4
            # imgs = []
            # for i in range(4):
            #     imgnp = np.array(
            #         fullPackets[offsetColor + imgBytes * i: offsetColor + imgBytes * (i + 1)], dtype=np.uint8)
            #     imgs.append(imgnp.reshape((256, 256, 4)))

            # cv.imshow('image_deirvlon 0', imgs[0])
            # cv.imshow('image_deirvlon 1', imgs[1])
            # cv.imshow('image_deirvlon 2', imgs[2])
            # cv.imshow('image_deirvlon 3', imgs[3])
            # cv.waitKey(1)
        
            # # https://docs.panda3d.org/1.10/python/programming/texturing/simple-texturing
            # # https://docs.panda3d.org/1.10/cpp/programming/advanced-loading/loading-resources-from-memory
            # pnm = p3d.PNMImage()
            # i = 0
            # imgData = fullPackets[offsetColor + imgBytes *
            #                       i: offsetColor + imgBytes * (i + 1)]
            # imgnp = np.array(
            #     fullPackets[offsetColor + imgBytes * i: offsetColor + imgBytes * (i + 1)], dtype=np.uint8)
            # #imgs.append(imgnp.reshape((256, 256, 4)))
            # pnm.read(p3d.StringStream(imgnp.reshape((256, 256, 4))))
            # tex = p3d.Texture()
            # tex.load(pnm)
            # mySvm.plane.setShaderInput('myTexture0', tex)
        

    #print(("Packets : {p0}, {p1}, {p2}, {p3}").format(p0=packet[0], p1=packet[1], p2=packet[2], p3=packet[3]))
    #print(index)
    #print(clientIP)

    # Sending a reply to client

t = threading.Thread(target=ReceiveData, args=())
t.start()

print("\n\nSVM Start!")
mySvm.run()