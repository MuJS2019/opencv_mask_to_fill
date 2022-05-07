# -*- coding: utf-8 -*- 

"""
需求：
    1、在尺寸为 2048 * 2048 的黑色背景图片中，  依次填充 images 中的气球图片，气球图
       片的间隔至少大于 20 个像素，填充完成并保存，如果填充溢出，可保存多张图片。。
    2、annotations.json 中对应每一个气球的标注的掩膜坐标信息，请根据 annotations 
       中的格式生成新的 json 标注文件，并确保新生成的 json 标注文件里的掩膜坐标信息对
       应需求 1 中保存的图片。
    3、请验证需求 2 中新生成 json 文件掩膜标注信息的正确性。
"""

import json
import numpy as np
import cv2 as cv

#初始化2048x2048的全黑图片img、对应的位置信息图片at和最后要保存为json的字典mapss
img=np.zeros([2048,2048,3],dtype="uint8")
at=np.zeros((2048,2048),dtype="uint8")
mapss={}
maps={}
maps['name']='polygon'
maps['all_points_x']=[]
maps['all_points_y']=[]

def merge(images, annotations_file):
    """
    input:
        images: 气球图片。
        annotations_file: 气球标注信息。
    """
    #读取图片并将轮廓信息载入为opencv轮廓信息标准格式
    img0=cv.imread('images/'+images)        
    contours=[list(t) for t in zip(annotations_file['all_points_x'],annotations_file['all_points_y'])]
    contours=np.array(contours).reshape(-1,1,2)
    #根据轮廓信息取到最小环绕矩形
    x, y, w, h = cv.boundingRect(contours)
    #根据最小环绕矩形与20像素的距离限制取出此图片的感兴趣区域roi并读取roi的长宽
    roi0=img0[y:y+h+20,x:x+w+20]
    rows,cols,channel=roi0.shape
    #重新标定轮廓信息以适应裁剪出的感兴趣区域roi
    contours=contours-[x,y]
    #根据轮廓信息生成掩模
    mask=cv.fillConvexPoly(np.zeros((rows,cols),dtype="uint8"), contours, 100)
    #根据掩模裁剪图片
    img0_fg = cv.bitwise_and(roi0, roi0, mask=mask)
    #根据位置信息图片at判定某一区域之前是否被填充过并确定这张图片应该填充在全黑图片上的位置
    i=0
    j=0
    #判定方式为at对应位置矩阵求和是否为零
    while(at[i:i+rows,j:j+cols].sum()!=0):
        #先走x方向 
        if(j+cols<2048):
            #步长为矩阵在x方向距离的均值，最小为1
            j=j+max(int(at[i:i+rows,j:j+cols].sum()/cols),1)
        #如果x方向不能走走y方向并将x重新置0
        if(j+cols>=2048):
            j=0
            #步长为矩阵在y方向距离的均值，最小为1
            i=i+max(int(at[i:i+rows,j:j+cols].sum()/rows),1)
        #如果xy方向均没有移动的位置了，则重置图片为全黑、位置信息图片at归零并保存当前图像与其中轮廓信息的字典
        if(i+rows>=2048 or j+cols>=2048):
            print('已经绘制完成一张图片，即将显示...')
            cv.imshow('img'+str(j),img)
            print('显示成功，请随便按一个键。')
            cv.waitKey(0)
            cv.destroyAllWindows()
            #根据当前x方向位置生成img图片后缀名
            cv.imwrite('img'+str(j)+'.jpg', img)
            #将字典保存到总字典中
            mapss['img'+str(j)+'.jpg']=maps
            #重置信息
            maps['all_points_x']=[]
            maps['all_points_y']=[]
            img[0:,0:,0:]=0
            at[0:,0:]=0
            i=0
            j=0
            break
    #at矩阵对应位置元素全部赋值为1,方便用sum计算步长,并且加入间隔20
    at[max(i-20,0):min(i+rows+20 ,2048),max(j-20,0):min(j+cols+20,2048)]=1
    #将全黑图片对应的填充位置裁剪出来
    roi=img[i:i+rows,j:j+cols]
    #填充 
    dst = cv.add(roi, img0_fg, dtype=cv.CV_32F)
    img[i:i+rows,j:j+cols] = dst
    #计算轮廓信息在全黑图片上的位置并保存到字典中
    contours=contours.reshape(-1,2)
    maps['all_points_x'].extend((contours[:,0]+j).tolist())
    maps['all_points_y'].extend((contours[:,1]+i).tolist())
    #验证轮廓位置正确性
    contours=[list(t) for t in zip(maps['all_points_x'],maps['all_points_y'])]
    contours=np.array(contours).reshape(-1,1,2)
    img1=cv.drawContours(np.zeros((2048,2048),dtype="uint8"), contours, -1, 255, 2)
    print('正在验证轮廓位置...')
    print('请随便按一个键，然后等待。')
    cv.imshow('contours',img1)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == '__main__':
    #读取json文件
    with open('annotations.json','r',encoding='utf8')as fp:
        json_data = json.load(fp)
    #将图片名称和位置信息提取出来传入merge
    for images,annotations_file in json_data.items():
        merge(images, annotations_file)
    print('已经绘制完成最后一张图片，即将显示...')
    cv.imshow('img',img)
    print('显示成功，请随便按一个键。')
    cv.waitKey(0)
    cv.destroyAllWindows()
    #保存最后一张绘出的img和其对应的位置信息到字典
    cv.imwrite('img.jpg', img)
    mapss['img.jpg']=maps
    #将字典保存为保存json
    b = json.dumps(mapss)
    f2 = open('new_json.json', 'w')
    f2.write(b)
    f2.close()
    print('已将所有信息保存至new_json.json。')
    print('全部完成，程序结束。')
