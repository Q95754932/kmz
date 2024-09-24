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
