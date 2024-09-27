from shapely.geometry import Polygon
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, Point, MultiPoint, LineString
from shapely.affinity import rotate
import matplotlib.pyplot as plt
from create_ import *
import numpy as np

# 创建一个图形对象，2行2列的子图布局
fig_, axs = plt.subplots(2, 3, figsize=(24, 8))
waypoint_color = "green"
# boundary_color = "red"
polygon_color = "blue"
point_size = 5


def draw(coords, fig, color, size, label, title=None, is_view=False, is_quiver=False):
    # 可视化平面坐标
    x_coords, y_coords = zip(*coords)  # 拆分为 x 和 y 坐标

    # 使用 quiver 绘制有向线段
    if is_quiver:
        # 构造有向线段的起点和方向向量
        u = np.diff(x_coords)  # x方向的变化量
        v = np.diff(y_coords)  # y方向的变化量
        x_start = x_coords[:-1]
        y_start = y_coords[:-1]
        fig.quiver(
            x_start,
            y_start,
            u,
            v,
            angles="xy",
            scale_units="xy",
            scale=1,
            color=color,
            width=0.002,
        )
    else:
        fig.scatter(x_coords, y_coords, c=color, marker="o", label=label, s=size)

    # 设置标题和坐标轴
    if title:
        fig.set_title(title)
    fig.set_xlabel("X")
    fig.set_ylabel("Y")
    fig.axis("equal")

    # 设置图例
    if label:
        fig.legend([label])

    # 设置网格
    fig.grid(True)

    # 如果启用视图调整，则自动调整子图布局
    if is_view:
        plt.tight_layout()
        plt.show()


#############################################################
## 计算形心
#############################################################
# wgs84_coords = [
#     (116.331475335, 35.290368739),
#     (116.361746745, 35.294927153),
#     (116.361263947, 35.297143999),
#     (116.330897318, 35.292667392),
# ]  # 点列表
wgs84_coords = [
    (116.338493334, 35.300982240),
    (116.335746752, 35.297227147),
    (116.340789305, 35.297237876),
]  # TODO 点列表

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

# TODO 定义角度方向  x轴正方向为0度，逆时针增加 单位度  范围从0-360
alpha = 20
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
## 旁向偏移在这里使用
#############################################################
heading_offset = 0  # TODO航向偏移, 单位 米  正数向外，负数向内
reduced_field_w = 10  # TODO w  相机缩减后的旁向视场范围 单位米   需要根据旁向重叠率计算出来
start_dir = "right"  # TODO 起始飞行点 是在航向的右边还是左边，默认右边

waypoints_list = []  # 航点存储
line_count = 0  # 记录有多少条长直航线
break_count = 0  # 超出界限两次跳出循环

# 计算出无人机飞行的最小y值和最大y值
# 根据起始飞行点判断计算出航点位置
start_y = min_y + reduced_field_w / 2 - reduced_field_w
# 减去reduced_field_w 是因为第一个点会导致y值要加上reduced_field_w
end_y = max_y - reduced_field_w / 2
if start_dir != "right":  # 起始点在航向的左侧  交换起点和终点的y值
    temp_y = start_y
    start_y = end_y
    end_y = temp_y

start_x = min_x
end_x = max_x

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
        if start_dir == "right":
            point_y = last_point_y + reduced_field_w
        else:
            point_y = last_point_y - reduced_field_w
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
    is_quiver=True,
)

#############################################################
## 对航点的x坐标进行收缩修正
## 只在修正里使用航向偏移，去除上述使用航向偏移的部分
#############################################################
# 创建多边形对象
polygon = Polygon(point_list)

adjusted_segments = []
miss_line = 0  # 有几条起始线和多边形没有交点
first_inter_line = None  # 第几条航线开始与多边形相交

# 遍历每一各航线，收缩航线
for i in range(0, len(waypoints_list), 2):
    p1 = Point(waypoints_list[i])
    p2 = Point(waypoints_list[i + 1])
    line = LineString([p1, p2])

    intersections = line.intersection(polygon)
    if len(intersections.coords) == 2:
        new_p1 = min([Point(intersections.coords[0]), Point(intersections.coords[-1])], key=lambda x: p1.distance(x))
        new_p2 = min([Point(intersections.coords[0]), Point(intersections.coords[-1])], key=lambda x: p2.distance(x))
        if first_inter_line is None:
            first_inter_line = i // 2  # 是个整数
    else:  # 没有交点或者只有一个交点，此时应该在边界
        if first_inter_line is None:  # 是首边界
            miss_line += 1  # 记录
            new_p1 = p1  # 使用原来的点位先进行占位
            new_p2 = p2
        else:  # 是尾边界,直接复制上一点的值
            new_p1 = Point(adjusted_segments[-2])
            new_p2 = Point(adjusted_segments[-1])

    adjusted_segments.append([new_p1.x, new_p1.y])
    adjusted_segments.append([new_p2.x, new_p2.y])

# 更正首边界无交点的航线,只更改X,不更改Y
for i in range(miss_line):
    if i % 2 == first_inter_line % 2:  # 当前的线段和交线的方向相同
        adjusted_segments[2 * i][0] = adjusted_segments[2 * first_inter_line][0]
        adjusted_segments[2 * i + 1][0] = adjusted_segments[2 * first_inter_line + 1][0]
    else:  # 当前的线段和交线的方向不同
        adjusted_segments[2 * i][0] = adjusted_segments[2 * first_inter_line + 1][0]
        adjusted_segments[2 * i + 1][0] = adjusted_segments[2 * first_inter_line][0]


# 增加航向偏移
offset_adjusted_segments = []

for i in range(0, len(adjusted_segments), 2):  # 步长为2
    if i % 4 == 0:  # 第一点是起始点,第二点是终止点
        point1 = (adjusted_segments[i][0] - heading_offset, adjusted_segments[i][1])
        point2 = (adjusted_segments[i + 1][0] + heading_offset, adjusted_segments[i + 1][1])
        if point2[0] - point1[0] < 0:  # 如果偏移完后顺序颠倒，则直接省略该点
            continue
    else:  # 第一点是终止点,第二点是起始点
        point1 = (adjusted_segments[i][0] + heading_offset, adjusted_segments[i][1])
        point2 = (adjusted_segments[i + 1][0] - heading_offset, adjusted_segments[i + 1][1])
        if point1[0] - point2[0] < 0:  # 如果偏移完后顺序颠倒，则直接省略该点
            continue
    offset_adjusted_segments.append(point1)
    offset_adjusted_segments.append(point2)

# 可视化航点
draw(
    coords=offset_adjusted_segments,
    fig=axs[1, 0],
    color="red",
    size=point_size,
    label="Modify point",
    title="Modify Coordinate",
    is_view=False,
    is_quiver=True,
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
multi_point = MultiPoint([Point(x, y) for x, y in offset_adjusted_segments])
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
    is_quiver=True,
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
    is_quiver=True,
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
