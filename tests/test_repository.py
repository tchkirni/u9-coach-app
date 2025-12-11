import tempfile
import unittest
from pathlib import Path
from unittest import mock

from storage import repository


class RepositoryTests(unittest.TestCase):
    def test_load_data_creates_structure_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file = Path(tmpdir) / "data.json"
            with mock.patch.object(repository, "DATA_FILE", temp_file):
                data = repository.load_data()

        self.assertEqual({"players": [], "matches": [], "trainings": []}, data)

    def test_save_and_load_round_trip(self):
        sample = {
            "players": [{"id": 1, "name": "Alex"}],
            "matches": [],
            "trainings": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file = Path(tmpdir) / "data.json"
            with mock.patch.object(repository, "DATA_FILE", temp_file):
                repository.save_data(sample)
                loaded = repository.load_data()

        self.assertEqual(sample, loaded)

    def test_get_next_id_and_find_helpers(self):
        players = [{"id": 1}, {"id": 4}]
        matches = [{"id": 2}, {"id": 5}]
        trainings = [{"id": 3}]

        self.assertEqual(repository.get_next_id(players), 5)
        self.assertEqual(repository.get_next_id([]), 1)

        data = {"players": players, "matches": matches, "trainings": trainings}
        self.assertEqual(repository.find_player(data, 4)["id"], 4)
        self.assertIsNone(repository.find_player(data, 99))
        self.assertEqual(repository.find_match(data, 5)["id"], 5)
        self.assertIsNone(repository.find_match(data, -1))
        self.assertEqual(repository.find_training(data, 3)["id"], 3)
        self.assertIsNone(repository.find_training(data, 0))


if __name__ == "__main__":
    unittest.main()
