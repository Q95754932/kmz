# import sys
# import os
# # 自动获取当前文件的所在路径，并添加文件夹到系统路径  __file__返回当前文件路径
# lib_directory = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(lib_directory)

from matplotlib.lines import Line2D
from shapely.geometry import Polygon
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, Point, MultiPoint, LineString
from shapely.affinity import rotate
import matplotlib.pyplot as plt
import numpy as np


class Calculator:
    """
    该类实现的功能是使用给定的多边形顶点坐标(wgs84坐标系的坐标),
    和一系列的飞行参数,进行航点规划,输出每个航点的坐标(wgs84坐标系的坐标)
    """

    def __init__(
        self,
        wgs84_coords,  # 边界点列表---经度纬度，需要按连线顺序输入，不能有交叉---单位: 度
        global_height=15,  # 航线高度---单位: 米
        flight_speed=None,  # 飞行速度---单位: 米/秒  取值为None时默认最大速度
        angle=None,  # 航线角度方向---x轴正方向为0度,逆时针增加,范围从0-360---单位: 度
        # 取值为None时自动按照第一点到第二点的方向
        heading_offset=0,  # 航向偏移---正数向外,负数向内---单位 :米
        camera_HFOV=52.8,  # 相机的水平FOV---单位: 度
        camera_VFOV=40.9,  # 相机的竖直FOV---单位: 度
        side_overlap_ratio=15,  # 单侧旁向重叠率---单位: 百分比
        heading_overlap_ratio=15,  # 单侧航向重叠率---单位: 百分比
        start_dir="right",  # 起始飞行点---是在航向的右边还是左边，默认右边
        camera_shoot_time=1,  # 相机拍照的间隔时间---单位: 秒
        view_size=(20, 8),  # 预览图大小---单位：英尺
    ):
        #############################################################
        ## 定义参数
        #############################################################
        self.wgs84_coords = wgs84_coords
        if angle is not None:
            self.angle = angle
        else:
            # 计算向量
            vector = np.array(self.wgs84_coords[1]) - np.array(self.wgs84_coords[0])
            # 计算夹角（弧度）
            angle_rad = np.arctan2(vector[1], vector[0])
            # 转换为度数
            angle_deg = np.degrees(angle_rad)
            # 确保角度为正数，并在 [0, 360) 范围内
            self.angle = angle_deg % 360

        self.global_height = global_height
        self.flight_speed = flight_speed
        self.heading_offset = heading_offset
        self.camera_HFOV = camera_HFOV
        self.camera_VFOV = camera_VFOV
        self.side_overlap_ratio = side_overlap_ratio
        self.heading_overlap_ratio = heading_overlap_ratio
        self.start_dir = start_dir
        self.camera_shoot_time = camera_shoot_time
        self.view_size = view_size

    #############################################################
    ## 定义可视化函数
    #############################################################

    # 航点列表和边界点列表（经纬度坐标）
    def draw(self):
        # 设定画图参数
        way_points = self.wgs84_waypoints
        polygon_points = self.wgs84_coords
        wp_label = "Waypoints"
        plg_label = "Polygon points"
        wp_color = "green"
        plg_color = "red"
        wp_size = 0.001
        plg_size = 50
        title = "WGS84 Coordinate"

        # 创建一个图形对象
        fig, axs = plt.subplots(1, 1, figsize=self.view_size)
        # 绘制航线
        x_coords, y_coords = zip(*way_points)  # 拆分为 x 和 y 坐标
        u = np.diff(x_coords)  # x方向的变化量
        v = np.diff(y_coords)  # y方向的变化量
        x_start = x_coords[:-1]
        y_start = y_coords[:-1]
        axs.quiver(
            x_start,
            y_start,
            u,
            v,
            angles="xy",
            scale_units="xy",
            scale=1,
            color=wp_color,
            width=wp_size,  # 默认是0.005
        )
        # 绘制多边形
        x_coords, y_coords = zip(*polygon_points)  # 拆分为 x 和 y 坐标
        axs.scatter(x_coords, y_coords, c=plg_color, marker="o", label=plg_label, s=plg_size)
        # 手动创建图例项
        legend_elements = [
            Line2D([0], [0], color=wp_color, lw=2, label=wp_label),  # 航点（quiver）
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=plg_color,
                markersize=10,
                label=plg_label,
            ),  # 多边形点
        ]
        # 添加图例到图形中
        axs.legend(handles=legend_elements)
        # 设置网格
        axs.grid(True)
        # 设置横纵坐标
        axs.set_title(title)
        axs.set_xlabel("Longitude")
        axs.set_ylabel("Latitude")
        axs.axis("equal")
        # 显示
        plt.tight_layout()
        plt.show()

    #############################################################
    ## 计算形心
    #############################################################

    def calculate_centroid(self):
        # 使用 shapely 创建一个多边形对象
        polygon = Polygon(self.wgs84_coords)
        assert polygon.is_valid, "输入的多边形不合法"  # 输入的点位没有交叉
        # 计算多边形的形心
        centroid = polygon.centroid
        self.centroid_x, self.centroid_y = centroid.x, centroid.y

    #############################################################
    ## 转换成平面坐标
    #############################################################

    def convert_to_plane_coords(self):
        # 定义 WGS84 地理坐标系 (EPSG:4326)
        wgs84 = CRS.from_epsg(4326)
        # 根据质心的纬度和经度来定义横轴墨卡托投影的坐标系
        self.mercator = CRS(proj="tmerc", lon_0=self.centroid_x, lat_0=self.centroid_y, ellps="WGS84")
        # 使用 Transformer 来执行坐标转换
        wgs84_to_mct = Transformer.from_crs(wgs84, self.mercator, always_xy=True)
        # 将经纬度坐标转换为平面坐标（横轴墨卡托）
        self.coords = [(wgs84_to_mct.transform(point[0], point[1])) for point in self.wgs84_coords]

    #############################################################
    ## 构建平面多边形，进行旋转
    #############################################################

    def build_and_rotate_polygon(self):
        # 使用 Shapely 创建多边形对象
        polygon = Polygon(self.coords)  # 会自动闭合多边形
        # 使用 Shapely 的 rotate 函数进行旋转
        rotated_polygon = rotate(polygon, -self.angle, origin=(0, 0), use_radians=False)  # 逆时针旋转
        # 去除封闭多边形的最后一个重复点位
        self.point_list = list(rotated_polygon.exterior.coords)[:-1]

    #############################################################
    ## 找到最小的外接矩形
    #############################################################

    def find_min_bounding_rectangle(self):
        point_np = np.array(self.point_list, dtype=np.float64)  # n,2
        self.min_x, self.min_y = point_np.min(axis=0)
        self.max_x, self.max_y = point_np.max(axis=0)

    #############################################################
    ## 在矩形中计算出各个航点位置
    #############################################################

    def calculate_waypoints_in_rectangle(self):
        # 相机缩减后的旁向视场范围 需要根据旁向重叠率计算出来
        self.reduced_field_w = (
            self.global_height
            * np.tan(self.camera_HFOV / 2 / 180 * np.pi)
            * 2
            * (1 - self.side_overlap_ratio / 100 * 2)
        )
        self.recmd_fight_speed = (
            self.global_height
            * np.tan(self.camera_VFOV / 2 / 180 * np.pi)
            * (2 - self.heading_overlap_ratio / 100 * 2)
            / self.camera_shoot_time
        )  # 保证航向重叠率不低于指定值的 建议最大飞行速度，单位 米/秒
        if self.flight_speed is not None:
            if self.flight_speed > self.recmd_fight_speed:
                print(
                    f"建议飞行速度上限：{self.recmd_fight_speed:.2f} 米/秒, 当前飞行速度：{self.flight_speed:.2f} 米/秒\n"
                )
            else:
                print(
                    f"建议飞行速度上限：{self.recmd_fight_speed:.2f} 米/秒, 当前飞行速度：{self.flight_speed:.2f} 米/秒, 请注意速度超出上限！\n"
                )
        else:
            self.flight_speed = 15 if self.recmd_fight_speed >= 15 else self.recmd_fight_speed
            print(
                f"建议飞行速度上限：{self.recmd_fight_speed:.2f} 米/秒, 飞行速度调整为：{self.flight_speed:.2f} 米/秒\n"
            )

        self.waypoints_list = []  # 航点存储
        line_count = 0  # 记录有多少条长直航线
        break_count = 0  # 超出界限两次跳出循环

        # 根据起始飞行点判断计算出航点位置
        start_y = self.min_y + self.reduced_field_w / 2 - self.reduced_field_w
        # 减去reduced_field_w 是因为第一个点会导致y值要加上reduced_field_w
        end_y = self.max_y - self.reduced_field_w / 2
        if self.start_dir != "right":  # 起始点在航向的左侧  交换起点和终点的y值
            temp_y = start_y
            start_y = end_y
            end_y = temp_y

        start_x = self.min_x
        end_x = self.max_x

        # 记录当前航点的y值
        last_point_y = start_y

        last_is_start = True  # 上一个点位是否在起始边  初始值是true
        now_is_start = True  # 判定是否在起始边

        # 当没有超出范围时，一直保持循环
        while True:
            if (last_point_y > end_y) if (self.start_dir == "right") else (last_point_y < end_y):
                break_count += 1
                if break_count >= 2:
                    break
            if now_is_start and last_is_start:  # 如果在起始边并且上一点也在起始边，说明下一点需要在终点边
                point_x = start_x
                if self.start_dir == "right":
                    point_y = last_point_y + self.reduced_field_w
                else:
                    point_y = last_point_y - self.reduced_field_w
                last_point_y = point_y
                # 下一点需要进行切换边
                last_is_start = now_is_start
                now_is_start = False
            elif not now_is_start and last_is_start:  # 在终点边
                point_x = end_x
                point_y = last_point_y
                # 下一点不需要进行切换边
                last_is_start = now_is_start
                # 记录航线
                line_count += 1
            elif not now_is_start and not last_is_start:  # 向上走一格
                point_x = end_x
                if self.start_dir == "right":
                    point_y = last_point_y + self.reduced_field_w
                else:
                    point_y = last_point_y - self.reduced_field_w
                # 更当前的值
                last_point_y = point_y
                # 下一点需要进行切换边
                last_is_start = now_is_start
                now_is_start = True
            elif now_is_start and not last_is_start:
                point_x = start_x
                point_y = last_point_y
                # 下一点不需要进行切换边
                last_is_start = now_is_start
                # 记录航线
                line_count += 1
            self.waypoints_list.append([point_x, point_y])

    #############################################################
    ## 对航点的x坐标进行收缩修正
    #############################################################

    def adjust_waypoints_x_coordinates(self):
        # 创建多边形对象
        polygon = Polygon(self.point_list)

        self.adjusted_segments = []

        # 遍历每一各航线，收缩航线
        for i in range(0, len(self.waypoints_list), 2):
            p1 = Point(self.waypoints_list[i])
            p2 = Point(self.waypoints_list[i + 1])
            line = LineString([p1, p2])

            intersections = line.intersection(polygon)
            # 相交、相离、包含返回line类型，相切返回点类型
            # 相交和包含是一样的，都返回端点坐标，相离返回坐标数为0
            if len(intersections.coords) >= 2 and isinstance(intersections, LineString):  # 相交
                new_p1 = min(
                    [Point(intersections.coords[0]), Point(intersections.coords[-1])],
                    key=lambda x: p1.distance(x),
                )
                new_p2 = min(
                    [Point(intersections.coords[0]), Point(intersections.coords[-1])],
                    key=lambda x: p2.distance(x),
                )
            else:  # 相切或者相离，此时必读在尾边界，首边界一定相交
                new_p1 = Point(self.adjusted_segments[-1][0], self.waypoints_list[i][1])
                new_p2 = Point(self.adjusted_segments[-2][0], self.waypoints_list[i][1])

            self.adjusted_segments.append([new_p1.x, new_p1.y])
            self.adjusted_segments.append([new_p2.x, new_p2.y])

        # 增加航向偏移  用于弥补无人机提前过弯
        self.offset_adjusted_segments = []

        for i in range(0, len(self.adjusted_segments), 2):  # 步长为2
            if i % 4 == 0:  # 第一点是起始点,第二点是终止点
                point1 = (self.adjusted_segments[i][0] - self.heading_offset, self.adjusted_segments[i][1])
                point2 = (self.adjusted_segments[i + 1][0] + self.heading_offset, self.adjusted_segments[i + 1][1])
                if point2[0] - point1[0] < 0:  # 如果偏移完后顺序颠倒，则直接省略该点
                    continue
            else:  # 第一点是终止点,第二点是起始点
                point1 = (self.adjusted_segments[i][0] + self.heading_offset, self.adjusted_segments[i][1])
                point2 = (self.adjusted_segments[i + 1][0] - self.heading_offset, self.adjusted_segments[i + 1][1])
                if point1[0] - point2[0] < 0:  # 如果偏移完后顺序颠倒，则直接省略该点
                    continue
            self.offset_adjusted_segments.append(point1)
            self.offset_adjusted_segments.append(point2)

    #############################################################
    ## 将所有航点旋转回原平面坐标系
    #############################################################

    def rotate_waypoints_back(self):
        # 使用 Shapely 创建点位
        multi_point = MultiPoint([Point(x, y) for x, y in self.offset_adjusted_segments])
        # 使用 Shapely 的 rotate 函数进行旋转
        re_multi_point = rotate(multi_point, self.angle, origin=(0, 0), use_radians=False)  # 逆时针旋转
        # 提取旋转后的点位坐标
        self.re_points = [(point.x, point.y) for point in re_multi_point.geoms]

    #############################################################
    ## 转换成WGS84坐标
    #############################################################

    def convert_to_wgs84(self):
        mct_to_wgs84 = Transformer.from_crs(self.mercator, CRS.from_epsg(4326), always_xy=True)
        self.wgs84_waypoints = [(mct_to_wgs84.transform(x, y)) for x, y in self.re_points]

    #############################################################
    ## 总流程调用
    #############################################################

    def calculate(self):
        self.calculate_centroid()
        self.convert_to_plane_coords()
        self.build_and_rotate_polygon()
        self.find_min_bounding_rectangle()
        self.calculate_waypoints_in_rectangle()
        self.adjust_waypoints_x_coordinates()
        self.rotate_waypoints_back()
        self.convert_to_wgs84()
        self.draw()
        return self.wgs84_waypoints, self.flight_speed


if __name__ == "__main__":
    # 调用示例
    calc = Calculator(
        wgs84_coords=[
            [112.950043079, 28.182389264],
            [112.950144979, 28.182422342],
            [112.950072576, 28.182565393],
            [112.949992129, 28.182539403],
        ],  # 坐标
        global_height=12,  # 航线高度---单位: 米
        flight_speed=None,  # 飞行速度---单位: 米/秒  取值为None时默认最大速度
        angle=None,  # 航线角度方向---x轴正方向为0度,逆时针增加,范围从0-360---单位: 度
        # 取值为None时自动按照第一点到第二点的方向
        heading_offset=0,  # 航向偏移---正数向外,负数向内---单位 :米
        camera_HFOV=52.8,  # 相机的水平FOV---单位: 度
        camera_VFOV=40.9,  # 相机的竖直FOV---单位: 度
        side_overlap_ratio=30,  # 单侧旁向重叠率---单位: 百分比
        heading_overlap_ratio=30,  # 单侧航向重叠率---单位: 百分比
        start_dir="right",  # 起始飞行点---是在航向的右边还是左边，默认右边
        camera_shoot_time=1,  # 相机拍照的间隔时间---单位: 秒
        view_size=(12, 6),  # 预览图大小---单位：英尺
    )
    waypoint_coords_wgs84 = calc.calculate()
    print(waypoint_coords_wgs84)
