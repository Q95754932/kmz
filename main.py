from lib import *

if __name__ == "__main__":
    #############################################################
    ## 定义变量和参数
    #############################################################

    input_coord_system = "cgcs2000"  # 'wgs84','cgcs2000','gcj02'
    input_coords = [
        [112.950043079, 28.182389264],
        [112.950144979, 28.182422342],
        [112.950072576, 28.182565393],
        [112.949992129, 28.182539403],
    ]  # 输入坐标

    takeoff_height = 12  # 起飞高度---单位: 米
    global_height = 12  # 航线高度---单位: 米
    flight_speed = 6  # 飞行速度---单位: 米/秒
    angle = None  # 航线角度方向---x轴正方向为0度,逆时针增加,范围从0-360---单位: 度
    # 取值为None时自动按照第一点到第二点的方向
    heading_offset = 0  # 航向偏移---正数向外,负数向内---单位 :米
    camera_HFOV = 52.8  # 相机的水平FOV---单位: 度
    camera_VFOV = 40.9  # 相机的竖直FOV---单位: 度
    side_overlap_ratio = 15  # 单侧旁向重叠率---单位: 百分比
    heading_overlap_ratio = 15  # 单侧航向重叠率---单位: 百分比
    start_dir = "right"  # 起始飞行点---是在航向的右边还是左边，默认右边
    camera_shoot_time = 1  # 相机拍照的间隔时间---单位: 秒
    view_size = (12, 6)  # 预览图大小---单位：英尺

    output_path = r"output/waypoints.kmz"
    output_coord_system = "cgcs2000"  # 'wgs84','cgcs2000','gcj02'

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
    waypoint_coords_wgs84 = calc.calculate()

    #############################################################
    ## 将输出WGS84坐标转换至目标坐标(WGS84、CGCS2000、GCJ02)
    #############################################################

    assert output_coord_system in ["wgs84", "cgcs2000", "gcj02"], "输出坐标系统错误"
    trans = CoordinateTransformer()
    coords_ = np.array(waypoint_coords_wgs84, dtype=np.float64)
    if input_coord_system == "wgs84":
        target_coords = coords_.tolist()
    elif input_coord_system == "cgcs2000":
        target_coords = trans.wgs84_to_cgcs2000(coords_).tolist()
    else:  # 'gcj02'
        target_coords = trans.wgs84_to_gcj02(coords_).tolist()

    #############################################################
    ## 生成KMZ文件
    #############################################################

    kmz = KmzCreator(takeoff_height, global_height, flight_speed, target_coords)
    kmz.create(output_path, remove_temp=True)
