from pyproj import Geod

# 创建一个Geod对象，使用WGS-84椭球体
geod = Geod(ellps="WGS84")
# 定义两点的经纬度
lat1, lon1 = (35.321917801, 116.355354363)
lat2, lon2 = (35.290369973, 116.331478921)

# 计算距离(此处为椭球表面距离，没有考虑高程差，与91卫图数据基本一致)  角度输出是-180度到180度
dir1, dir2, distance = geod.inv(lon1, lat1, lon2, lat2)
print(f"两点之间的距离: {distance} 米")
print(f"方位角1: {dir1} °")
print(f"方位角2: {dir2} °")
