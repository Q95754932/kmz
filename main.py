from lib.calculate_ import *

if __name__ == "__main__":
    # 调用示例
    calc = Calculator(
        gcj02_coords=[
            (112.950043079, 28.182389264),
            (112.950144979, 28.182422342),
            (112.950072576, 28.182565393),
            (112.949992129, 28.182539403),
        ],  # 坐标
        takeoff_height=12,  # 起飞高度---单位: 米
        global_height=12,  # 航线高度---单位: 米
        flight_speed=5,  # 飞行速度---单位: 米/秒
        angle=None,  # 航线角度方向---x轴正方向为0度,逆时针增加,范围从0-360---单位: 度
        # 取值为None时自动按照第一点到第二点的方向
        heading_offset=0,  # 航向偏移---正数向外,负数向内---单位 :米
        camera_HFOV=52.8,  # 相机的水平FOV---单位: 度
        camera_VFOV=40.9,  # 相机的竖直FOV---单位: 度
        side_overlap_ratio=30,  # 单侧旁向重叠率---单位: 百分比
        heading_overlap_ratio=30,  # 单侧航向重叠率---单位: 百分比
        start_dir="right",  # 起始飞行点---是在航向的右边还是左边，默认右边
        camera_shoot_time=1,  # 相机拍照的间隔时间---单位: 秒
        output_path="output/gcj02.kmz",  # 文件输出路径
    )
    calc.calculate()
