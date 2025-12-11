import unittest

from core import constants
from core.models import best_position_from_scores, compute_position_scores


class ComputePositionScoresTests(unittest.TestCase):
    def test_scores_use_weighted_average_and_rounding(self):
        player = {
            "base_ratings": {
                "Passes courtes": 4,
                "Passes longues": 3,
                "Endurance": 5,
            }
        }

        scores = compute_position_scores(player)

        expected_milieu_num = 4 * constants.POSITION_WEIGHTS["Milieu"]["Passes courtes"]
        expected_milieu_num += 3 * constants.POSITION_WEIGHTS["Milieu"]["Passes longues"]
        expected_milieu_num += 5 * constants.POSITION_WEIGHTS["Milieu"]["Endurance"]
        expected_milieu_den = (
            constants.POSITION_WEIGHTS["Milieu"]["Passes courtes"]
            + constants.POSITION_WEIGHTS["Milieu"]["Passes longues"]
            + constants.POSITION_WEIGHTS["Milieu"]["Endurance"]
        )
        expected_milieu_score = round(expected_milieu_num / expected_milieu_den, 2)

        expected_gardien_num = 4 * constants.POSITION_WEIGHTS["Gardien"]["Passes courtes"]
        expected_gardien_num += 3 * constants.POSITION_WEIGHTS["Gardien"]["Passes longues"]
        expected_gardien_num += 5 * constants.POSITION_WEIGHTS["Gardien"]["Endurance"]
        expected_gardien_den = (
            constants.POSITION_WEIGHTS["Gardien"]["Passes courtes"]
            + constants.POSITION_WEIGHTS["Gardien"]["Passes longues"]
            + constants.POSITION_WEIGHTS["Gardien"]["Endurance"]
        )
        expected_gardien_score = round(expected_gardien_num / expected_gardien_den, 2)

        self.assertEqual(scores["Milieu"], expected_milieu_score)
        self.assertEqual(scores["Gardien"], expected_gardien_score)

    def test_missing_ratings_return_none_scores(self):
        player = {"base_ratings": {}}

        scores = compute_position_scores(player)

        self.assertTrue(all(score is None for score in scores.values()))


class BestPositionTests(unittest.TestCase):
    def test_returns_highest_score(self):
        scores = {"Gardien": 2.5, "Défenseur": 3.1, "Milieu": None}

        best = best_position_from_scores(scores)

        self.assertEqual(best, "Défenseur")

    def test_returns_none_when_no_valid_scores(self):
        self.assertIsNone(best_position_from_scores({"Gardien": None}))


if __name__ == "__main__":
    unittest.main()
