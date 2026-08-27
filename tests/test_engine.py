import unittest

from valuo_sipri.engine import estimate_opinion, haversine_km


class Comparable:
    def __init__(self, price, construction_m2, latitude=22.1508, longitude=-100.9842):
        self.operation = "VENTA"
        self.property_type = "CASA"
        self.price = price
        self.construction_m2 = construction_m2
        self.land_m2 = construction_m2
        self.bedrooms = 3
        self.latitude = latitude
        self.longitude = longitude
        self.reference = "Prueba"
        self.verified = False


class EngineTests(unittest.TestCase):
    def test_haversine_same_point(self):
        self.assertEqual(haversine_km(22.1, -100.9, 22.1, -100.9), 0)

    def test_estimate_generates_range(self):
        data = {"operation": "VENTA", "property_type": "CASA", "latitude": 22.1508, "longitude": -100.9842, "construction_m2": 180, "land_m2": 160, "bedrooms": 3, "quality": "MEDIA", "amenities": ["Jardín"]}
        result = estimate_opinion(data, [Comparable(3600000, 180), Comparable(4000000, 200)], [])
        self.assertGreater(result["estimate"], 0)
        self.assertLess(result["lower"], result["estimate"])
        self.assertGreater(result["upper"], result["estimate"])


if __name__ == "__main__":
    unittest.main()
