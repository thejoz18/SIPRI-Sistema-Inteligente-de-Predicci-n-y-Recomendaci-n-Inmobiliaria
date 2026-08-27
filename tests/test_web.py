import unittest

from fastapi.testclient import TestClient

from valuo_sipri.app import app


class WebTests(unittest.TestCase):
    def test_home_and_create_opinion(self):
        with TestClient(app) as client:
            home = client.get("/")
            self.assertEqual(home.status_code, 200)
            self.assertIn("VALUO SIPRI", home.text)
            response = client.post("/opinions", data={
                "client_name": "Prueba SIPCO", "address": "Domicilio de prueba SLP", "operation": "VENTA",
                "property_type": "CASA", "zone_name": "Lomas del Tecnologico", "latitude": "22.1508", "longitude": "-100.9842",
                "land_m2": "160", "construction_m2": "180", "bedrooms": "3", "bathrooms": "2", "parking_spaces": "2",
                "age_years": "5", "quality": "MEDIA", "amenities": "Jardin",
            }, files={"photos": ("omitido.txt", b"", "text/plain")}, follow_redirects=False)
            self.assertEqual(response.status_code, 303, response.text)
            self.assertTrue(response.headers["location"].startswith("/opinions/"))
            pdf = client.get(response.headers["location"] + "/pdf")
            self.assertEqual(pdf.status_code, 200)
            self.assertEqual(pdf.headers["content-type"], "application/pdf")
            self.assertGreater(len(pdf.content), 1000)


if __name__ == "__main__":
    unittest.main()
