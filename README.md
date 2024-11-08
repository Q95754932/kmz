# 无人机航点规划

### 1.注意事项

1.**==飞行区域必须为凸多边形==**，顶点数大于等于三的多边形区域。

### 2.使用说明

1.使用如下指令安装所需依赖。

```
pip install -r requirements.txt
```

2.根据main.py中的注释，调整 “参数” 部分内容。

3.运行main.py文件，生成kmz后缀文件。

4.将kmz文件导入大疆遥控器。

5.调整相机云台向下，开启定时拍摄。

6.选中导入航线检查相关信息后执行航线。

### 3.使用建议

1.支持91卫图中的天地图和高德地图选点，**==优先使用天地图进行飞行区域的选点==**，避免坐标转换，航点更加准确。

### 4.其他信息

1.天地图的坐标系为CGCS2000，高德地图的坐标系为GCJ02，无人机的坐标系为WGS84。

2.utils文件夹中的extrat_img_info.py文件可以提取出照片中的经度、纬度等信息。

### 5.存在问题

1.使用 “协调转弯，不过点，提前转弯” 的航点类型上传航线任务时，可能会遇到 “航线中存在入弯距离过小的航点” 报错信息，==需要调整或者删除不符合的航点（通常是最后一个航点）==，也可以将航点类型更换成 ”直线飞行，到点停“ 。

2.不管是天地图还是高德地图，实际航点位置与规划航点位置基本一致，只有最后一个航的点位置会有较大偏差（偏差距离在1.5米左右），说明飞机的定位性能优秀。

3.天地图规划的航点位置与理论位置能对上，高德地图规划的航点位置与理论位置存在2米左右的偏差（根据拍摄图像得出）。上述后者存在偏差，大概率是坐标转换造成的（航点规划和执行时使用的是WGS84坐标系，因此需要将高德地图的GCJ02坐标转换成WGS84坐标，坐标之间的转换不可逆，会存在一些偏差）。

4.遥控器显示的航点位置与理论位置存在2米左右的偏差（根据拍摄图像得出，遥控器的图像有2米左右的偏差）。