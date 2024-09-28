# from shapely.geometry import Point, LineString, Polygon

# point_a = Point([-1, 0])
# point_b = Point([0, 0])

# polyg = Polygon(
#     [
#         (0, 0),
#         (2, 2),
#         (2, -2),
#     ]
# )
# print(f"{polyg.contains(point_a)=}")
# print(f"{polyg.contains(point_b)=}")

# line = LineString([point_a, point_b])

# intersections = line.intersection(polyg)

# print(f"{len(intersections.coords)=}")
# print(f"{intersections.coords[0]=}")
# print(f"{intersections.coords[1]=}")
# print(f"{intersections.coords[2]=}")
############################################################
# import numpy as np

# print(f"{np.tan(45/180*np.pi)=}")
############################################################
# import matplotlib.pyplot as plt

# # 定义起点
# x_start = [1]
# y_start = [1]

# # 定义向量分量
# u = [2]  # x方向的变化
# v = [1]  # y方向的变化

# # 创建两个子图
# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

# # 第二个子图：angles="xy"
# ax2.quiver(x_start, y_start, u, v, angles="xy", scale_units="xy", scale=1)
# ax2.set_title('angles="xy"')
# ax2.set_xlim(-1, 10)
# ax2.set_ylim(-1, 10)
# ax2.set_aspect("auto")  # 不强制保持比例相等
# ax2.grid(True)

# plt.show()
############################################################
