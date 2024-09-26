from shapely.geometry import Polygon
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, Point, MultiPoint, LineString
from shapely.affinity import rotate
import matplotlib.pyplot as plt
from create_ import *

# 创建一个图形对象，2行2列的子图布局
fig_, axs = plt.subplots(2, 3, figsize=(24, 8))
waypoint_color = "green"
# boundary_color = "red"
polygon_color = "blue"
point_size = 5


def draw(coords, fig, color, size, label, title=None, is_view=False):
    # 可视化平面坐标
    x_coords, y_coords = zip(*coords)  # 拆分为 x 和 y 坐标
    fig.scatter(x_coords, y_coords, c=color, marker="o", label=label, s=size)
    if title:
        fig.set_title(title)
    fig.set_xlabel("X")
    fig.set_ylabel("Y")
    fig.axis("equal")
    fig.legend()
    fig.grid(True)
    if is_view:
        # 自动调整子图布局
        plt.tight_layout()
        plt.show()


#############################################################
## 计算形心
#############################################################
wgs84_coords = [
    (116.331475335, 35.290368739),
    (116.361746745, 35.294927153),
    (116.361263947, 35.297143999),
    (116.330897318, 35.292667392),
]  # 点列表
# 使用 shapely 创建一个多边形对象
polygon = Polygon(wgs84_coords)
assert polygon.is_valid, "输入的多边形不合法"  # 输入的点位没有交叉
# 计算多边形的形心
centroid = polygon.centroid
centroid_x, centroid_y = centroid.x, centroid.y
# 输出形心的经纬度
# print(f"形心的经度: {centroid_x}, 形心的纬度: {centroid_y}")

#############################################################
## 转换成平面坐标
#############################################################

# 定义 WGS84 地理坐标系 (EPSG:4326)
wgs84 = CRS.from_epsg(4326)
# 根据质心的纬度和经度来定义横轴墨卡托投影的坐标系
mercator = CRS(proj="tmerc", lon_0=centroid_x, lat_0=centroid_y, ellps="WGS84")

# 使用 Transformer 来执行坐标转换
wgs84_to_mct = Transformer.from_crs(wgs84, mercator, always_xy=True)
# 将经纬度坐标转换为平面坐标（横轴墨卡托）
coords = [(wgs84_to_mct.transform(point[0], point[1])) for point in wgs84_coords]
# print(f"平面坐标列表: x, y: {coords}")
# 可视化平面坐标
draw(
    coords=coords,
    fig=axs[0, 0],
    color=polygon_color,
    size=point_size,
    label="MCT point",
    title="MCT Coordinate",
    is_view=False,
)
#############################################################
## 构建平面多边形，进行旋转
#############################################################

# 定义角度方向  x轴正方向为0度，逆时针增加 单位度  范围从0-360
alpha = 0
# 使用 Shapely 创建多边形对象
polygon = Polygon(coords)  # 会自动闭合多边形
# 使用 Shapely 的 rotate 函数进行旋转
rotated_polygon = rotate(polygon, -alpha, origin=(0, 0), use_radians=False)  # 逆时针旋转

# 去除封闭多边形的最后一个重复点位
point_list = list(rotated_polygon.exterior.coords)[:-1]
# 输出旋转后的多边形顶点
# print(f"旋转后的多边形顶点坐标: {point_list}")  # 获取到坐标
# 可视化
draw(
    coords=point_list,
    fig=axs[0, 1],
    color=polygon_color,
    size=point_size,
    label="Rotate point",
    title="Rotate Coordinate",
    is_view=False,
)

#############################################################
## 找到最小的外接矩形
#############################################################
import numpy as np

point_np = np.array(point_list, dtype=np.float64)  # n,2
min_x, min_y = point_np.min(axis=0)
max_x, max_y = point_np.max(axis=0)
# print(f"min x,y{min_x, min_y}")
# print(f"max x,y{max_x, max_y}")

#############################################################
## 在矩形中计算出各个航点位置
#############################################################
point_offset = [0, 0]  # 航向偏移,旁向偏移  单位 米  正数向外，负数向内
reduced_field_w = 50  # w  相机缩减后的旁向视场范围 单位米   需要根据旁向重叠率计算出来
start_dir = "right"  # 起始飞行点 是在航向的右边还是左边，默认右边
waypoints_list = []  # 航点存储
line_count = 0  # 记录有多少条长直航线
break_count = 0  # 超出界限

# 计算出无人机飞行的最小y值和最大y值
# 根据起始飞行点判断计算出航点位置
start_y = min_y + reduced_field_w / 2 - point_offset[1]
end_y = max_y - reduced_field_w / 2 + point_offset[1]
if start_dir != "right":  # 起始点在航向的左侧  交换起点和终点的y值
    temp_y = start_y
    start_y = end_y
    end_y = temp_y
# 只能通过偏移进行起点和终点的矫正，否则默认在外接矩形的边上
start_x = min_x - point_offset[0]
end_x = max_x + point_offset[0]

# 记录当前航点的y值
last_point_y = start_y

last_is_start = True  # 上一个点位是否在起始边  初始值是true
now_is_start = True  # 判定是否在起始边

# 当没有超出范围时，一直保持循环
while True:
    if (last_point_y > end_y) if (start_dir == "right") else (last_point_y < end_y):
        break_count += 1
        if break_count >= 2:
            break
    if now_is_start and last_is_start:  # 如果在起始边并且上一点也在起始边，说明下一点需要在终点边
        point_x = start_x
        point_y = last_point_y
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
        if start_dir == "right":
            point_y = last_point_y + reduced_field_w
        else:
            point_y = last_point_y - reduced_field_w
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
    waypoints_list.append([point_x, point_y])

# print(f"旋转后的航点坐标：{waypoints_list}")
# print(f"长直航线的数量：{line_count}")
# 可视化航点
draw(
    coords=waypoints_list,
    fig=axs[0, 2],
    color=waypoint_color,
    size=point_size,
    label="Waypoint point",
    title="Waypoint Coordinate",
    is_view=False,
)

#############################################################
## 对航点的x坐标进行收缩修正
## 只在修正里使用航向偏移，去除上述使用航线偏移的部分
#############################################################
# 创建多边形对象
polygon = Polygon(point_list)

adjusted_segments = []

# 遍历每一对线段点
for i in range(0, len(waypoints_list), 2):
    p1 = Point(waypoints_list[i])
    p2 = Point(waypoints_list[i + 1])
    line = LineString([p1, p2])

    # 检查点是否在多边形内
    if polygon.contains(p1):
        new_p1 = p1  # 保留原点
    else:
        # 如果点在多边形外，找到线段与多边形边界的交点
        intersections = line.intersection(polygon)
        if intersections.is_empty:
            new_p1 = Point(adjusted_segments[-2][0], p1.y)  # 采用上一点的值
            new_p2 = Point(adjusted_segments[-1][0], p2.y)  # 采用上一点的值
        elif isinstance(intersections, Point):
            new_p1 = intersections  # 单个交点
        elif isinstance(intersections, MultiPoint):
            # 多个交点时，选择与 p1 最近的点
            new_p1 = min(intersections, key=lambda x: p1.distance(x))
        elif isinstance(intersections, LineString):
            # 如果返回的是线段（LineString），取最近的端点
            new_p1 = min(
                [Point(intersections.coords[0]), Point(intersections.coords[-1])], key=lambda x: p1.distance(x)
            )
        else:
            print(f"修正航点时出错，取消原航修正！")
            new_p1 = p1  # 保留原点

    if polygon.contains(p2):
        new_p2 = p2  # 保留原点
    else:
        # 找到线段与多边形的交点
        intersections = line.intersection(polygon)
        if intersections.is_empty:
            new_p1 = Point(adjusted_segments[-2][0], p1.y)  # 采用上一点的值
            new_p2 = Point(adjusted_segments[-1][0], p2.y)  # 采用上一点的值
        elif isinstance(intersections, Point):
            new_p2 = intersections  # 单个交点
        elif isinstance(intersections, MultiPoint):
            # 多个交点时，选择与 p2 最近的点
            new_p2 = min(intersections, key=lambda x: p2.distance(x))
        elif isinstance(intersections, LineString):
            # 如果返回的是线段，取最近的端点
            new_p2 = min(
                [Point(intersections.coords[0]), Point(intersections.coords[-1])], key=lambda x: p2.distance(x)
            )
        else:
            print(f"修正航点时出错，取消原航修正！")
            new_p2 = p2  # 保留原点

    # 存储调整后的线段
    adjusted_segments.append([new_p1.x, new_p1.y])
    adjusted_segments.append([new_p2.x, new_p2.y])

# 可视化航点
draw(
    coords=adjusted_segments,
    fig=axs[1, 0],
    color="red",
    size=point_size,
    label="Modify point",
    title="Modify Coordinate",
    is_view=False,
)
draw(
    coords=waypoints_list,
    fig=axs[1, 0],
    color=waypoint_color,
    size=point_size,
    label="Waypoint point",
    is_view=False,
)
#############################################################
## 将所有航点旋转回原平面坐标系
#############################################################

# 使用 Shapely 创建点位
multi_point = MultiPoint([Point(x, y) for x, y in adjusted_segments])
# 使用 Shapely 的 rotate 函数进行旋转
re_multi_point = rotate(multi_point, alpha, origin=(0, 0), use_radians=False)  # 逆时针旋转
# 提取旋转后的点位坐标
re_points = [(point.x, point.y) for point in re_multi_point.geoms]
# 输出旋转后的多边形顶点
# print(f"还原后的航点位坐标: {re_points}")  # 获取到坐标
# 可视化航点
draw(
    coords=re_points,
    fig=axs[1, 1],
    color=waypoint_color,
    size=point_size,
    label="Re-rotate point",
    title="Re-rotate Coordinate",
    is_view=False,
)

#############################################################
## 转换成WGS84坐标
#############################################################

mct_to_wgs84 = Transformer.from_crs(mercator, wgs84, always_xy=True)
wgs84_waypoints = [(mct_to_wgs84.transform(x, y)) for x, y in re_points]
# print(f"航点的WGS84坐标: {wgs84_waypoints}")
# 可视化航点
draw(
    coords=wgs84_waypoints,
    fig=axs[1, 2],
    color=waypoint_color,
    size=point_size,
    label="Waypoints",
    title="WGS84 Coordinate",
    is_view=False,
)
draw(
    coords=wgs84_coords,
    fig=axs[1, 2],
    color=polygon_color,
    size=point_size,
    label="Polygon points",
    is_view=True,
)


#############################################################
## 生成kmz文件
#############################################################
# takeoff_height = 15  # 起飞高度
# global_height = 20  # 飞行高度
# flight_speed = 3  # 飞行速度

# kmz = KmzCreator(takeoff_height, global_height, flight_speed, wgs84_waypoints)
# kmz.create("output/file.kmz", True)
