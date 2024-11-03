from lib import *

#############################################################
## 参数
#############################################################

input_coord_system = "wgs84"  # 根据输入坐标的坐标系进行选择：'wgs84','cgcs2000','gcj02'
input_coords = [
    [112.944666091529, 28.1851235963937],
    [112.945041600791, 28.1851718761559],
    [112.94482702407, 28.1865451671716],
    [112.944416646091, 28.1863681413766],
]  # 飞行区域的经纬度坐标---单位：度

takeoff_height = 20  # 起飞高度---单位: 米
global_height = 20  # 航线高度---单位: 米
flight_speed = 3  # 飞行速度,范围从 0-15 ---单位: 米/秒
# 上述变量取值为None时默认最大速度
angle = (0, 1)
"""
三种angle的使用示例
1. angle = 0  # 航线方向角度---东经方向为0度,逆时针增加,范围从 0-360 ---单位: 度
2. angle = (0,1)  # 航线方向索引---航线方向的起点索引和终点索引(输入点位的索引)
3. angle = 
((112.944666091529, 28.1851235963937),(112.94482702407, 28.1865451671716))
# 航线方向点位---航线方向的起点经纬度坐标和终点经纬度坐标
"""
heading_offset = 0  # 航向偏移---正数向外,负数向内---单位 :米
camera_HFOV = 52.8  # 相机水平FOV---单位: 度
camera_VFOV = 40.9  # 相机竖直FOV---单位: 度
side_overlap_ratio = 15  # 单侧旁向重叠率---单位: 百分比
heading_overlap_ratio = 15  # 单侧航向重叠率---单位: 百分比
start_dir = "right"  # 起始飞行点---是在航向的右边还是左边，默认右边
camera_shoot_time = 1  # 相机拍照间隔时间---单位: 秒
view_size = (12, 6)  # 预览图大小---单位：英尺

output_path = r"output/waypoints.kmz"  # 输出文件路径
output_coord_system = "wgs84"  # 根据目标坐标的坐标系进行选择：'wgs84','cgcs2000','gcj02'

#############################################################
#############################################################

if __name__ == "__main__":
    #############################################################
    ## 将输入坐标(WGS84、CGCS2000、GCJ02)转换至WGS84坐标
    #############################################################

    assert input_coord_system in ["wgs84", "cgcs2000", "gcj02"], "输入坐标系统错误"
    trans = CoordinateTransformer()
    coords_ = np.array(input_coords, dtype=np.float64)
    if input_coord_system == "wgs84":
        wgs84_coords = coords_.tolist()
    elif input_coord_system == "cgcs2000":
        wgs84_coords = trans.cgcs2000_to_wgs84(coords_).tolist()
    else:  # 'gcj02'
        wgs84_coords = trans.gcj02_to_wgs84(coords_).tolist()

    #############################################################
    ## 根据WGS84坐标以及给定参数进行航点规划
    #############################################################

    calc = Calculator(
        wgs84_coords=wgs84_coords,
        global_height=global_height,
        flight_speed=flight_speed,
        angle=angle,
        heading_offset=heading_offset,
        camera_HFOV=camera_HFOV,
        camera_VFOV=camera_VFOV,
        side_overlap_ratio=side_overlap_ratio,
        heading_overlap_ratio=heading_overlap_ratio,
        start_dir=start_dir,
        camera_shoot_time=camera_shoot_time,
        view_size=view_size,
    )
    waypoint_coords_wgs84, flight_speed = calc.calculate()

    #############################################################
    ## 将输出WGS84坐标转换至目标坐标(WGS84、CGCS2000、GCJ02)
    #############################################################

    assert output_coord_system in ["wgs84", "cgcs2000", "gcj02"], "输出坐标系统错误"
    trans = CoordinateTransformer()
    coords = np.array(waypoint_coords_wgs84, dtype=np.float64)
    if output_coord_system == "wgs84":
        target_coords = coords.tolist()
    elif output_coord_system == "cgcs2000":
        target_coords = trans.wgs84_to_cgcs2000(coords).tolist()
    else:  # 'gcj02'
        target_coords = trans.wgs84_to_gcj02(coords).tolist()

    #############################################################
    ## 生成KMZ文件
    #############################################################

    kmz = KmzCreator(takeoff_height, global_height, flight_speed, target_coords)
    kmz.create(output_path, remove_temp=True)
