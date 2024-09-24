import math


def haversine(lat1, lon1, lat2, lon2, alt1=0, alt2=0):
    # 将经纬度转换为弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # 计算经纬度差值
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine公式计算地表距离
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 地球半径（公里）
    R = 6371
    surface_distance = R * c

    # 计算高度差
    height_diff = abs(alt2 - alt1) / 1000  # 将高度从米转换为公里

    # 计算三维直线距离
    total_distance = math.sqrt(surface_distance**2 + height_diff**2)

    return total_distance


# 示例：两点的经纬度和高度差
lat1, lon1, alt1 = 116.331478921, 35.290369973, 39.750  # 上海，海平面
lat2, lon2, alt2 = 116.361746628, 35.294931479, 38.749  # 另一点，高度500米

distance = haversine(lat1, lon1, lat2, lon2, alt1, alt2)
print(f"两点之间的三维空间距离: {distance:.2f} 公里")
