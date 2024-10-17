import exifread
import os
import glob

"""
用于提取jpg图像中的经度、纬度、高度信息
"""


def convert_to_degrees(value):
    """
    将GPS坐标从度、分、秒格式转换为十进制度数
    """
    d = float(value[0])
    m = float(value[1])
    # 处理秒数中的分数
    s_num, s_den = value[2].num, value[2].den
    s = float(s_num) / float(s_den)
    return d + (m / 60.0) + (s / 3600.0)


# 指定包含图片的文件夹
folder = "data/gd"  # 请将此路径替换为您的变量文件夹路径

# 仅遍历文件夹中的 .jpg 图片文件
jpg_files = glob.glob(os.path.join(folder, "*.jpg"))
# 如果需要同时检查大写扩展名的文件，请取消注释以下行
# jpg_files += glob.glob(os.path.join(folder, '*.JPG'))

for filepath in jpg_files:
    with open(filepath, "rb") as f:
        tags = exifread.process_file(f)
        # 检查是否存在GPS信息
        if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
            # 提取GPS纬度和经度参考方向
            lat_ref = tags.get("GPS GPSLatitudeRef").values
            lon_ref = tags.get("GPS GPSLongitudeRef").values
            # 提取GPS纬度和经度值
            lat = tags["GPS GPSLatitude"].values
            lon = tags["GPS GPSLongitude"].values
            # 将坐标转换为十进制度数
            lat_dd = convert_to_degrees(lat)
            lon_dd = convert_to_degrees(lon)
            # 根据参考方向调整正负号
            if lat_ref != "N":
                lat_dd = -lat_dd
            if lon_ref != "E":
                lon_dd = -lon_dd
            # 打印结果，保留15位小数
            if "GPS GPSAltitude" in tags:
                alt = tags["GPS GPSAltitude"].values[0].num / tags["GPS GPSAltitude"].values[0].den
                print(f"文件: {filepath}, 经度: {lon_dd:.15f}, 纬度: {lat_dd:.15f}, 高度: {alt:.15f}")
            else:
                print(f"文件: {filepath}, 经度: {lon_dd:.15f}, 纬度: {lat_dd:.15f}, 高度: None")
        else:
            print(f"文件 {filepath} 中没有GPS信息")
