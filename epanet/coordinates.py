import shapefile
from epanet.layer_base import LayerBase


class Coordinates(LayerBase):
    class Coordinate(object):
        def __init__(self, data):
            self.id = data["id"]
            self.lon = round(data["lon"], 6)
            self.lat = round(data["lat"], 6)
            self.elevation = data["elevation"] or 0
            self.lon_utm = round(data["lon_utm"], 3)
            self.lat_utm = round(data["lat_utm"], 3)
            self.demand = 0.0
            self.pattern = ""

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
            coord = Coordinates.Coordinate(data)
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
                    _shp.record(coord.id, coord.elevation, coord.pattern, coord.demand, '')
            _shp.close()
        self.createProjection(filename)

    def add_demands(self, connections):
        for conn in connections:
            target_key = ",".join([str(conn.lon), str(conn.lat)])
            for key in self.coordMap:
                if key == target_key:
                    self.coordMap[key].demand = conn.demands
