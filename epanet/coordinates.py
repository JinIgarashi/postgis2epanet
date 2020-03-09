import shapefile
from epanet.layer_base import LayerBase


class Coordinates(LayerBase):
    class Coordinate(object):
        def __init__(self, id, lon, lat, altitude, lon_utm, lat_utm):
            self.id = id
            self.lon = round(lon, 6)
            self.lat = round(lat, 6)
            self.altitude = altitude or 0
            self.lon_utm = round(lon_utm, 3)
            self.lat_utm = round(lat_utm, 3)
            self.demand = 0.0
            self.pattern = ""

        @staticmethod
        def create_header_junction(f):
            f.writelines("[JUNCTIONS]\n")
            f.writelines(";{0}\t{1}\t{2}\t{3}\n"
                         .format("ID\t".expandtabs(20),
                                 "Elev\t".expandtabs(12),
                                 "Demand\t".expandtabs(12),
                                 "Pattern\t".expandtabs(16)))

        def add_junction(self, f):
            f.writelines(" {0}\t{1}\t{2}\t{3}\t;\n"
                         .format("{0}\t".format(self.id).expandtabs(20),
                                 "{0}\t".format(self.altitude).expandtabs(12),
                                 "{0}\t".format(self.demand).expandtabs(12),
                                 "{0}\t".format(self.pattern).expandtabs(16)))

        @staticmethod
        def create_header_coordinates(f):
            f.writelines("[COORDINATES]\n")
            f.writelines(";{0}\t{1}\t{2}\n"
                         .format("Node\t".expandtabs(20),
                                 "X-Coord\t".expandtabs(16),
                                 "Y-Coord\t".expandtabs(16)))

        def add_coordinate(self, f):
            f.writelines(" {0}\t{1}\t{2}\n"
                         .format("{0}\t".format(self.id).expandtabs(20),
                                 "{0}\t".format(self.lon).expandtabs(16),
                                 "{0}\t".format(self.lat).expandtabs(16)))

    def __init__(self, wss_id, config):
        super().__init__("junctions", wss_id, config)
        self.coordMap = {}

    def get_coord_by_id(self, id):
        for key in self.coordMap:
            coord = self.coordMap[key]
            if id == coord.id:
                return coord

    def get_data(self, db):
        query = self.get_sql().format(str(self.wss_id))
        result = db.execute(query)
        for data in result:
            coord = Coordinates.Coordinate("Node-" + str(data[0]), data[1], data[2], data[3], data[4], data[5])
            key = ",".join([str(coord.lon), str(coord.lat)])
            self.coordMap[key] = coord

    def add_coordinate(self, coord):
        target_key = ",".join([str(coord.lon), str(coord.lat)])
        del_key = []
        for key in self.coordMap:
            if key == target_key:
                del_key.append(target_key)
        for key in del_key:
            self.coordMap.pop(key)
        self.coordMap[target_key] = coord

    def export_junctions(self, f):
        Coordinates.Coordinate.create_header_junction(f)
        for key in self.coordMap:
            coord = self.coordMap[key]
            if "Node" in coord.id:
                coord.add_junction(f)
        f.writelines("\n")

    def export_coordinates(self, f):
        Coordinates.Coordinate.create_header_coordinates(f)
        for key in self.coordMap:
            coord = self.coordMap[key]
            coord.add_coordinate(f)
        f.writelines("\n")

    def export_shapefile(self, f, del_coords_id):
        filename = self.get_file_path(f)
        with shapefile.Writer(filename) as _shp:
            _shp.autoBalance = 1
            _shp.field('dc_id', 'C', 254)
            _shp.field('elevation', 'N', 20)
            _shp.field('pattern', 'C', 254)
            _shp.field('demand', 'N', 20, 9)
            _shp.field('demand_pto', 'N', 20, 9)
            for key in self.coordMap:
                coord = self.coordMap[key]
                if "Node" in coord.id:
                    if coord.id in del_coords_id:
                        continue
                    _shp.point(float(coord.lon), float(coord.lat))
                    _shp.record(coord.id, coord.altitude, coord.pattern, coord.demand, '')
            _shp.close()
        self.createProjection(filename)

    def add_demands(self, connections):
        for conn in connections:
            target_key = ",".join([str(conn.lon), str(conn.lat)])
            for key in self.coordMap:
                if key == target_key:
                    self.coordMap[key].demand = conn.demands
