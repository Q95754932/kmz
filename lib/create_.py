import xml.etree.ElementTree as ET
import os
from typing import List, Tuple
from time import time
import xml.dom.minidom as minidom
import zipfile
import shutil


class KmzCreator:
    def __init__(
        self,
        takeoff_height: float,  # 起飞高度 单位 m
        global_height: float,  # 飞行高度  单位 m
        flight_speed: float,  # 飞行速度 单位 m/s
        coordinates: List[Tuple[float, float]],  # WGS84坐标系下的经纬坐标 单位 °
    ) -> None:
        super().__init__()
        self.kml_template_path = "template/kml_template.kml"  # 模板文件的路径
        self.kml_output_path = "wpmz/template.kml"

        self.wpml_template_path = "template/wpml_template.wpml"  # 模板文件的路径
        self.wpml_output_path = "wpmz/waylines.wpml"

        self.takeoff_height = takeoff_height
        self.global_height = global_height
        self.flight_speed = flight_speed
        self.coordinates = coordinates

    def prettify_xml(self, elem):
        """格式化XML 添加缩进和换行 并去除多余的空行"""
        rough_string = ET.tostring(elem, "utf-8")
        reparsed = minidom.parseString(rough_string)
        # 格式化输出并指定编码
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="UTF-8")
        # 去除多余的空行
        return b"\n".join([line for line in pretty_xml.splitlines() if line.strip()])

    def create_kml(self):
        print("正在导出kml文件...")
        # 参数检查
        assert os.path.exists(self.kml_template_path), "模板文件不存在"
        assert 2 <= self.takeoff_height <= 1500, "起飞高度错误"
        assert -1500 <= self.global_height <= 1500, "飞行高度错误"
        assert 1 <= self.flight_speed <= 15, "飞行速度错误"
        assert len(self.coordinates) >= 2, "点位坐标错误"
        # 点位参数
        point_param = {
            "wpml:ellipsoidHeight": str(self.global_height),
            "wpml:height": str(self.global_height),
            "wpml:useGlobalHeight": "1",
            "wpml:useGlobalSpeed": "1",
            "wpml:useGlobalHeadingParam": "1",
            "wpml:useGlobalTurnParam": "1",
            "wpml:useStraightLine": "0",
            "wpml:isRisky": "0",
        }
        # 解析XML文件
        tree = ET.parse(self.kml_template_path)
        root = tree.getroot()
        # 命名空间声明
        namespaces = {"wpml": "http://www.dji.com/wpmz/1.0.6", "kml": "http://www.opengis.net/kml/2.2"}
        # 注册命名空间前缀
        ET.register_namespace("wpml", namespaces["wpml"])
        ET.register_namespace("", namespaces["kml"])
        # 修改文件创建时间
        _time = round(time() * 1000)
        create_time = root.find(".//wpml:createTime", namespaces)
        assert create_time is not None, "模板错误"
        create_time.text = str(_time)
        update_time = root.find(".//wpml:updateTime", namespaces)
        assert update_time is not None, "模板错误"
        update_time.text = str(_time + 1)
        # 修改起飞安全高度
        takeoff_height_element = root.find(".//wpml:takeOffSecurityHeight", namespaces)
        assert takeoff_height_element is not None, "模板错误"
        takeoff_height_element.text = str(self.takeoff_height)
        # 修改全局飞行高度
        global_height_element = root.find(".//wpml:globalHeight", namespaces)
        assert global_height_element is not None, "模板错误"
        global_height_element.text = str(self.global_height)
        # 修改航线飞行速度
        flight_speed_element = root.find(".//wpml:autoFlightSpeed", namespaces)
        assert flight_speed_element is not None, "模板错误"
        flight_speed_element.text = str(self.flight_speed)

        folder_element = root.find(".//kml:Folder", namespaces)
        assert folder_element is not None, "模板错误"
        # 添加Placemark
        for i, coord in enumerate(self.coordinates):
            new_placemark = ET.Element("Placemark")
            point = ET.SubElement(new_placemark, "Point")
            coord_element = ET.SubElement(point, "coordinates")
            coord_element.text = f"{coord[0]},{coord[1]}"
            # 创建点位索引
            wpml_index = ET.SubElement(new_placemark, "wpml:index")
            wpml_index.text = str(i)
            # 创建其它标签
            for name, value in point_param.items():
                element = ET.SubElement(new_placemark, name)
                element.text = value
            # 将Placemark添加到Folder
            payload_param = folder_element.find(".//wpml:payloadParam", namespaces)
            folder_element.insert(list(folder_element).index(payload_param), new_placemark)
        # 获取文件路径的目录部分
        directory = os.path.dirname(self.kml_output_path)
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)
        # 使用minidom格式化并保存XML
        xml_string = self.prettify_xml(root)
        # 将格式化后的XML字符串写入文件
        with open(self.kml_output_path, "wb") as f:
            f.write(xml_string)
        print("kml文件已成功导出!")

    def create_wpml(self):
        print("正在导出wpml文件...")
        # 参数检查
        assert os.path.exists(self.wpml_template_path), "模板文件不存在"
        assert 2 <= self.takeoff_height <= 1500, "起飞高度错误"
        assert -1500 <= self.global_height <= 1500, "飞行高度错误"
        assert 1 <= self.flight_speed <= 15, "飞行速度错误"
        assert len(self.coordinates) >= 2, "点位坐标错误"
        # 点位参数
        point_param = {
            "wpml:executeHeight": str(self.global_height),
            "wpml:waypointSpeed": str(self.flight_speed),
            "wpml:waypointHeadingParam": {
                "wpml:waypointHeadingMode": "followWayline",
                "wpml:waypointHeadingAngle": "0",
                "wpml:waypointPoiPoint": "0.000000,0.000000,0.000000",
                "wpml:waypointHeadingAngleEnable": "0",
                "wpml:waypointHeadingPoiIndex": "0",
            },
            "wpml:waypointTurnParam": {
                "wpml:waypointTurnMode": "coordinateTurn",
                "wpml:waypointTurnDampingDist": "0",
            },
            "wpml:useStraightLine": "1",
            "wpml:waypointGimbalHeadingParam": {
                "wpml:waypointGimbalPitchAngle": "0",
                "wpml:waypointGimbalYawAngle": "0",
            },
            "wpml:isRisky": "0",
            "wpml:waypointWorkType": "0",
        }
        # 解析XML文件
        tree = ET.parse(self.wpml_template_path)
        root = tree.getroot()
        # 命名空间声明
        namespaces = {"wpml": "http://www.dji.com/wpmz/1.0.6", "kml": "http://www.opengis.net/kml/2.2"}
        # 注册命名空间前缀
        ET.register_namespace("wpml", namespaces["wpml"])
        ET.register_namespace("", namespaces["kml"])
        # 修改起飞安全高度
        takeoff_height_element = root.find(".//wpml:takeOffSecurityHeight", namespaces)
        assert takeoff_height_element is not None, "模板错误"
        takeoff_height_element.text = str(self.takeoff_height)
        # 修改航线飞行速度
        flight_speed_element = root.find(".//wpml:autoFlightSpeed", namespaces)
        assert flight_speed_element is not None, "模板错误"
        flight_speed_element.text = str(self.flight_speed)

        folder_element = root.find(".//kml:Folder", namespaces)
        assert folder_element is not None, "模板错误"
        # 添加Placemark
        for i, coord in enumerate(self.coordinates):
            new_placemark = ET.Element("Placemark")
            point = ET.SubElement(new_placemark, "Point")
            coord_element = ET.SubElement(point, "coordinates")
            coord_element.text = f"{coord[0]},{coord[1]}"
            # 创建点位索引
            wpml_index = ET.SubElement(new_placemark, "wpml:index")
            wpml_index.text = str(i)
            # 创建其它标签元素
            for name, value in point_param.items():
                element = ET.SubElement(new_placemark, name)
                if isinstance(value, dict):  # 嵌套参数
                    for name_, value_ in value.items():
                        element_ = ET.SubElement(element, name_)
                        element_.text = value_
                else:
                    element.text = value
            # 将Placemark添加到Folder
            folder_element.append(new_placemark)
        # 获取文件路径的目录部分
        directory = os.path.dirname(self.wpml_output_path)
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)
        # 使用minidom格式化并保存XML
        xml_string = self.prettify_xml(root)
        # 将格式化后的XML字符串写入文件
        with open(self.wpml_output_path, "wb") as f:
            f.write(xml_string)
        print("wpml文件已成功导出!")

    def zip_file(self, kmz_output_path: str = "output/file.kmz"):
        print(f"正在导出kmz文件...")
        # 检查文件
        assert os.path.exists(self.wpml_output_path) and os.path.exists(self.kml_output_path), "目标文件不存在"
        assert os.path.splitext(kmz_output_path)[-1] == ".kmz", "输出文件格式错误"
        # 确保输出ZIP文件名是绝对路径或相对于当前工作目录
        if not os.path.isabs(kmz_output_path):
            kmz_output_path = os.path.join(os.getcwd(), kmz_output_path)
        # 获取文件路径的目录部分
        directory = os.path.dirname(kmz_output_path)
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)
        # 创建一个 ZipFile 对象，并设置模式为 'w' 表示写入
        with zipfile.ZipFile(kmz_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 遍历文件夹中的所有文件和子文件夹
            for root, dirs, files in os.walk("wpmz"):
                # 遍历当前目录下的所有文件
                for file in files:
                    # 获取文件的完整路径
                    file_path = os.path.join(root, file)
                    # 计算文件在ZIP中的相对路径
                    arcname = os.path.relpath(file_path, start="")
                    # 将文件添加到ZIP文件中
                    zipf.write(file_path, arcname)
        print(f"kmz文件已成功导出!")

    def create(self, kmz_output_path: str = "output/file.kmz", remove_temp: bool = True):
        self.create_kml()
        self.create_wpml()
        self.zip_file(kmz_output_path)
        if remove_temp:  # 删除生成文件的父文件夹及其内容
            parent_folder = os.path.dirname(self.kml_output_path)
            if os.path.exists(parent_folder):
                shutil.rmtree(parent_folder)
            print(f"已删除缓存文件!")


if __name__ == "__main__":
    takeoff_height = 15  # 起飞高度
    global_height = 20  # 飞行高度
    flight_speed = 3  # 飞行速度
    coordinates = [
        (112.944532599761, 28.1860361476966),
        (112.944612851315, 28.1860619890799),
        (112.944685090702, 28.1859187973407),
        (112.944583439, 28.1858859074767),
        (112.944531264732, 28.1860042320262),
    ]  # 这里是给定的WGS84坐标系下的经纬度坐标

    kmz = KmzCreator(takeoff_height, global_height, flight_speed, coordinates)
    kmz.create("output/file.kmz", True)
