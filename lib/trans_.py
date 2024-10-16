import numpy as np

# 设置 numpy 的浮点数输出精度
np.set_printoptions(precision=15)  # 设置为 15 位小数显示


class CoordinateTransformer:
    def __init__(self) -> None:
        pass
        """
        每次转换都会产生一定的偏移，需要尽量减少转换的次数
        """

    # 经度偏移量
    def lng_transform(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        ret = 300.0 + x + 2.0 * y + 0.1 * x**2 + 0.1 * x * y + 0.1 * np.sqrt(np.abs(x))
        ret += (20.0 * np.sin(6.0 * x * np.pi) + 20.0 * np.sin(2.0 * x * np.pi)) * 2.0 / 3.0
        ret += (20.0 * np.sin(x * np.pi) + 40.0 * np.sin(x / 3.0 * np.pi)) * 2.0 / 3.0
        ret += (150.0 * np.sin(x / 12.0 * np.pi) + 300.0 * np.sin(x / 30.0 * np.pi)) * 2.0 / 3.0
        return ret

    # 纬度偏移量
    def lat_transform(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y**2 + 0.1 * x * y + 0.2 * np.sqrt(np.abs(x))
        ret += (20.0 * np.sin(6.0 * x * np.pi) + 20.0 * np.sin(2.0 * x * np.pi)) * 2.0 / 3.0
        ret += (20.0 * np.sin(y * np.pi) + 40.0 * np.sin(y / 3.0 * np.pi)) * 2.0 / 3.0
        ret += (160.0 * np.sin(y / 12.0 * np.pi) + 320.0 * np.sin(y / 30.0 * np.pi)) * 2.0 / 3.0
        return ret

    # GCJ-02 坐标转换为 WGS-84
    def gcj02_to_wgs84(self, coords: np.ndarray) -> np.ndarray:
        # 检查输入数据的数据类型
        assert coords.dtype == np.float64, "经纬度数据类型应为float64"

        lng, lat = coords[:, 0], coords[:, 1]
        dlng = self.lng_transform(lng - 105.0, lat - 35.0)
        dlat = self.lat_transform(lng - 105.0, lat - 35.0)

        radlat = lat / 180.0 * np.pi
        magic = np.sin(radlat)
        magic = 1 - 0.00669342162296594323 * magic**2
        sqrtmagic = np.sqrt(magic)

        dlng = (dlng * 180.0) / ((6378245.0 / sqrtmagic) * np.cos(radlat) * np.pi)
        dlat = (dlat * 180.0) / ((6335552.717000426 / (magic * sqrtmagic)) * np.pi)

        mglng = lng + dlng
        mglat = lat + dlat

        # 返回转换后的坐标
        return np.vstack([lng * 2 - mglng, lat * 2 - mglat]).T

    # WGS-84 坐标转换为 GCJ-02
    def wgs84_to_gcj02(self, coords: np.ndarray) -> np.ndarray:
        # 检查输入数据的数据类型
        assert coords.dtype == np.float64, "经纬度数据类型应为float64"

        lng, lat = coords[:, 0], coords[:, 1]
        dlng = self.lng_transform(lng - 105.0, lat - 35.0)
        dlat = self.lat_transform(lng - 105.0, lat - 35.0)

        radlat = lat / 180.0 * np.pi
        magic = np.sin(radlat)
        magic = 1 - 0.00669342162296594323 * magic**2
        sqrtmagic = np.sqrt(magic)

        dlng = (dlng * 180.0) / ((6378245.0 / sqrtmagic) * np.cos(radlat) * np.pi)
        dlat = (dlat * 180.0) / ((6335552.717000426 / (magic * sqrtmagic)) * np.pi)

        mglng = lng + dlng
        mglat = lat + dlat

        # 返回转换后的坐标
        return np.vstack([mglng, mglat]).T

    # WGS-84 坐标转换为 CGCS2000
    def wgs84_to_cgcs2000(self, coords: np.ndarray) -> np.ndarray:
        # 检查输入数据的数据类型
        assert coords.dtype == np.float64, "经纬度数据类型应为float64"

        # WGS84 椭球参数
        a_wgs84 = 6378137.0
        f_wgs84 = 1 / 298.257223563
        e2_wgs84 = 2 * f_wgs84 - f_wgs84**2

        # CGCS2000 椭球参数
        a_cgcs2000 = 6378137.0
        f_cgcs2000 = 1 / 298.257222101
        e2_cgcs2000 = 2 * f_cgcs2000 - f_cgcs2000**2

        # 七参数
        tx = -0.00016  # 米
        ty = 0.00026
        tz = 0.00011
        rx = 0.0  # 角秒
        ry = 0.0
        rz = 0.0
        ds = 0.0  # ppm

        # 角度转换为弧度，尺度转换为无量纲
        rx_rad = rx * np.pi / (180 * 3600)
        ry_rad = ry * np.pi / (180 * 3600)
        rz_rad = rz * np.pi / (180 * 3600)
        s = ds * 1e-6

        # 假设高程为 0
        h = 0.0

        output_coords = np.zeros_like(coords)
        for i in range(coords.shape[0]):
            lon, lat = coords[i, 0], coords[i, 1]
            # 转换为地心直角坐标系
            X, Y, Z = self.geodetic_to_geocentric(lon, lat, h, a_wgs84, e2_wgs84)
            # 进行七参数转换
            X2, Y2, Z2 = self.helmert_transformation(X, Y, Z, tx, ty, tz, rx_rad, ry_rad, rz_rad, s)
            # 转换回大地坐标系
            lon2, lat2, h2 = self.geocentric_to_geodetic(X2, Y2, Z2, a_cgcs2000, e2_cgcs2000)
            output_coords[i, 0] = lon2
            output_coords[i, 1] = lat2
        return output_coords

    # CGCS2000 坐标转换为 WGS-84
    def cgcs2000_to_wgs84(self, coords: np.ndarray) -> np.ndarray:
        # 检查输入数据的数据类型
        assert coords.dtype == np.float64, "经纬度数据类型应为float64"

        # CGCS2000 椭球参数
        a_cgcs2000 = 6378137.0
        f_cgcs2000 = 1 / 298.257222101
        e2_cgcs2000 = 2 * f_cgcs2000 - f_cgcs2000**2

        # WGS84 椭球参数
        a_wgs84 = 6378137.0
        f_wgs84 = 1 / 298.257223563
        e2_wgs84 = 2 * f_wgs84 - f_wgs84**2

        # 七参数的反向
        tx = 0.00016  # 米
        ty = -0.00026
        tz = -0.00011
        rx = 0.0  # 角秒
        ry = 0.0
        rz = 0.0
        ds = 0.0  # ppm

        # 角度转换为弧度，尺度转换为无量纲
        rx_rad = rx * np.pi / (180 * 3600)
        ry_rad = ry * np.pi / (180 * 3600)
        rz_rad = rz * np.pi / (180 * 3600)
        s = ds * 1e-6

        # 假设高程为 0
        h = 0.0

        output_coords = np.zeros_like(coords)
        for i in range(coords.shape[0]):
            lon, lat = coords[i, 0], coords[i, 1]
            # 转换为地心直角坐标系
            X, Y, Z = self.geodetic_to_geocentric(lon, lat, h, a_cgcs2000, e2_cgcs2000)
            # 进行七参数转换
            X2, Y2, Z2 = self.helmert_transformation(X, Y, Z, tx, ty, tz, rx_rad, ry_rad, rz_rad, s)
            # 转换回大地坐标系
            lon2, lat2, h2 = self.geocentric_to_geodetic(X2, Y2, Z2, a_wgs84, e2_wgs84)
            output_coords[i, 0] = lon2
            output_coords[i, 1] = lat2
        return output_coords

    # 地理坐标转换为地心直角坐标
    def geodetic_to_geocentric(self, lon, lat, h, a, e2):
        lon_rad = np.deg2rad(lon)
        lat_rad = np.deg2rad(lat)
        N = a / np.sqrt(1 - e2 * np.sin(lat_rad) ** 2)
        X = (N + h) * np.cos(lat_rad) * np.cos(lon_rad)
        Y = (N + h) * np.cos(lat_rad) * np.sin(lon_rad)
        Z = (N * (1 - e2) + h) * np.sin(lat_rad)
        return X, Y, Z

    # 地心直角坐标转换为地理坐标
    def geocentric_to_geodetic(self, X, Y, Z, a, e2):
        # 计算经度
        lon = np.arctan2(Y, X)
        # 迭代计算纬度
        p = np.sqrt(X**2 + Y**2)
        lat = np.arctan2(Z, p * (1 - e2))
        lat_prev = 0.0
        while np.abs(lat - lat_prev) > 1e-12:
            lat_prev = lat
            N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
            h = p / np.cos(lat) - N
            lat = np.arctan2(Z, p * (1 - e2 * N / (N + h)))
        # 计算高程
        N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
        h = p / np.cos(lat) - N
        # 转换为度
        lat_deg = np.rad2deg(lat)
        lon_deg = np.rad2deg(lon)
        return lon_deg, lat_deg, h

    # 七参数转换
    def helmert_transformation(self, X, Y, Z, tx, ty, tz, rx, ry, rz, s):
        X2 = tx + (1 + s) * (X - rz * Y + ry * Z)
        Y2 = ty + (1 + s) * (rz * X + Y - rx * Z)
        Z2 = tz + (1 + s) * (-ry * X + rx * Y + Z)
        return X2, Y2, Z2

    # GCJ-02 坐标转换为 CGCS2000
    def gcj02_to_cgcs2000(self, coords: np.ndarray) -> np.ndarray:
        # 首先将 GCJ-02 转换为 WGS-84，然后再转换为 CGCS2000
        coords_wgs84 = self.gcj02_to_wgs84(coords)
        coords_cgcs2000 = self.wgs84_to_cgcs2000(coords_wgs84)
        return coords_cgcs2000

    # CGCS2000 坐标转换为 GCJ-02
    def cgcs2000_to_gcj02(self, coords: np.ndarray) -> np.ndarray:
        # 首先将 CGCS2000 转换为 WGS-84，然后再转换为 GCJ-02
        coords_wgs84 = self.cgcs2000_to_wgs84(coords)
        coords_gcj02 = self.wgs84_to_gcj02(coords_wgs84)
        return coords_gcj02


if __name__ == "__main__":
    # 示例调用
    trans = CoordinateTransformer()
    # 示例输入：多个坐标点，合并为 shape=(n, 2) 的数组
    coords_gcj = np.array(
        [
            [112.950043079, 28.182389264],
            [112.950144979, 28.182422342],
            [112.950072576, 28.182565393],
        ],
        dtype=np.float64,
    )
    # GCJ-02 转 WGS-84
    coords_wgs = trans.gcj02_to_wgs84(coords_gcj)
    print(f"WGS-84坐标系下的经纬度: \n{coords_wgs}")
    # 示例输入：WGS-84 坐标点，合并为 shape=(n, 2) 的数组
    coords_wgs = np.array(
        [
            [112.950043079, 28.182389264],
            [112.950144979, 28.182422342],
            [112.950072576, 28.182565393],
        ],
        dtype=np.float64,
    )
    # WGS-84 转 GCJ-02
    coords_gcj2 = trans.wgs84_to_gcj02(coords_wgs)
    print(f"GCJ-02坐标系下的经纬度: \n{coords_gcj2}")

    coords_wgs = np.array(
        [
            [112.950043079, 28.182389264],
            [112.950144979, 28.182422342],
            [112.950072576, 28.182565393],
            [112.949992129, 28.182539403],
        ],
        dtype=np.float64,
    )

    # WGS-84 转 CGCS2000
    coords_cgcs = trans.wgs84_to_cgcs2000(coords_wgs)
    print(f"CGCS2000坐标系下的经纬度: \n{coords_cgcs}")

    # CGCS2000 转 WGS-84
    coords_wgs2 = trans.cgcs2000_to_wgs84(coords_cgcs)
    print(f"WGS-84坐标系下的经纬度: \n{coords_wgs2}")
