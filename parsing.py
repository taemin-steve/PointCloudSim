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

# print('Pandas Version :', panda3d.__version__)

# ############ Main Thread
# class SurroundView(ShowBase):
#     def __init__(self):
#         super().__init__()
        
#         # 카메라 위치 조정 
#         self.cam.setPos(0, 0, 80)
#         self.cam.lookAt(p3d.LPoint3f(0, 0, 0), p3d.LVector3f(0, 1, 0))
#         #self.trackball.node().setMat(self.cam.getMat())
#         #self.trackball.node().reset()
#         #self.trackball.node().set_pos(0, 30, 0)
        
#         #보트 로드
#         self.boat = self.loader.loadModel("avikus_boat.glb")
#         bbox = self.boat.getTightBounds()
#         print(bbox)
#         center = (bbox[0] + bbox[1]) * 0.5
#         self.boat.setPos(-center)
#         self.boat.reparentTo(self.render)
#         bbox = self.boat.getTightBounds()
        
#         self.axis = self.loader.loadModel('zup-axis')
#         self.axis.setPos(0, 0, 0)
#         #self.axis.setScale(.001)
#         self.axis.reparentTo(base.render)
        
#         #쉐이더 설정 
#         #my_shader = Shader.load(Shader.SL_GLSL,
#         #                        vertex="shaders/texturing-vert.glsl",
#         #                        fragment="shaders/texturing-frag.glsl")
#         vertex_format = p3d.GeomVertexFormat.getV3t2()
#         vdata = p3d.GeomVertexData('triangle_data', vertex_format, p3d.Geom.UHStatic)
#         vdata.setNumRows(2)
#         vertex = p3d.GeomVertexWriter(vdata, 'vertex')
#         texcoord = p3d.GeomVertexWriter(vdata, 'texcoord')

#         waterZ = bbox[0].z + (bbox[1].z - bbox[0].z) * 0.2
#         vertex.addData3(-10, 10, waterZ)
#         vertex.addData3(10, 10, waterZ)
#         vertex.addData3(10, -10, waterZ)
#         vertex.addData3(-10, -10, waterZ)
#         texcoord.addData2(0, 0)
#         texcoord.addData2(1, 0)
#         texcoord.addData2(1, 1)
#         texcoord.addData2(0, 1)
        
#         rectTris = p3d.GeomTriangles(p3d.Geom.UHStatic)
#         rectTris.addVertices(0, 1, 2)
#         rectTris.addVertices(0, 2, 3)
        
#         geom = p3d.Geom(vdata)
#         geom.addPrimitive(rectTris)
#         geomNode = p3d.GeomNode("my plane")
#         geomNode.addGeom(geom)
#         self.plane = p3d.NodePath(geomNode) # note nodePath is the instance for node (obj resource)
#         self.plane.setTwoSided(True)
#         self.plane.reparentTo(self.render)

# mySvm = SurroundView()
# mySvm.run()

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
        print(len(packetInit)) #이건 총 개수만 적어주는 듯. 
        
        if index == 0xffffffff:
            print("packet start")
            packetNum = int.from_bytes(packetInit[4:8], "little") #116개 들어옴
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
                bytesAddressPair = UDPServerSocket.recvfrom(bufferSize) #매번 다시 받아오는듯
                packet = bytesAddressPair[0]
                address = bytesAddressPair[1]
                UDPServerSocket.sendto(bytesToSend, addressInit)
                index = int.from_bytes(packet[0:4], "little")
                if (index != packetIndex) :
                    print(("Error {id}").format(id = index))
                packetIndex += 1
                fullPackets += packet[4:] # 패킷의 첫번째 부분은 index니깐 빼주고 더해주는듯.
                #print(("index {i}, num bytes {b}").format(i=index, b=len(packet)))
                
            print(("Bytes of All Packets: {d}").format(d=len(fullPackets)))
            # to do 
            lidarRes = 100
            lidarchs = 32
            imageWidth = 256
            imageHeight = 256

            # point cloud buffer : fullPackets[0:bytesPoints]
            # depth buffer : fullPackets[bytesPoints:bytesPoints + bytesDepthmap] ... 4 of (lidarRes * lidarchs * 4 bytes) 

            pc_position = []
            pc_color = []
            for i in range(0,len(fullPackets[0:bytesPoints]),16):
                pc_position.append([struct.unpack('f',fullPackets[i:i+4]), struct.unpack('f',fullPackets[i+4:i+8]),struct.unpack('f',fullPackets[i+8:i+12])])
                pc_color.append([fullPackets[i + 12],fullPackets[i +13],fullPackets[i +14],fullPackets[i +15]])

            pc_position = np.array(pc_position )
            pc_position = pc_position .reshape(-1,3)
            pc_color = np.array(pc_color)

            print(pc_color.shape)

            # offsetColor = bytesPoints + bytesDepthmap
            # imgBytes = imageWidth * imageHeight * 4
            # imgs = []
            # for i in range(4):
            #     imgnp = np.array(
            #         fullPackets[offsetColor + imgBytes * i: offsetColor + imgBytes * (i + 1)], dtype=np.uint8) # 얘 입장에서야 FColor고, 
            #     imgs.append(imgnp.reshape((256, 256, 4))) # 4체널로 들어오고 있다는거거든. 각체널이 1인가

            # cv.imshow('image_deirvlon 0', imgs[0])
            # cv.imshow('image_deirvlon 1', imgs[1])
            # cv.imshow('image_deirvlon 2', imgs[2])
            # cv.imshow('image_deirvlon 3', imgs[3])
            # cv.waitKey(1)
        
        

    #print(("Packets : {p0}, {p1}, {p2}, {p3}").format(p0=packet[0], p1=packet[1], p2=packet[2], p3=packet[3]))
    #print(index)
    #print(clientIP)

    # Sending a reply to client

t1 = threading.Thread(target=ReceiveData, args=())
t1.start()
