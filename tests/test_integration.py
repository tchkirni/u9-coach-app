import copy
import unittest
from datetime import date
from unittest import mock

from storage import repository
from ui.pages import exports, matches, players, profiles, trainings


class FakeContext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeStreamlit:
    def __init__(self):
        self.session_state = {"mobile_mode": True}

    def header(self, *args, **kwargs):
        pass

    def subheader(self, *args, **kwargs):
        pass

    def title(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def success(self, *args, **kwargs):
        pass

    def markdown(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass

    def table(self, *args, **kwargs):
        pass

    def dataframe(self, *args, **kwargs):
        pass

    def bar_chart(self, *args, **kwargs):
        pass

    def download_button(self, *args, **kwargs):
        return None

    def form(self, *args, **kwargs):
        return FakeContext()

    def form_submit_button(self, *args, **kwargs):
        return False

    def button(self, *args, **kwargs):
        return False

    def selectbox(self, label, options, index=0, **kwargs):
        if not options:
            return None
        if index < len(options):
            return options[index]
        return options[0]

    def checkbox(self, label, value=False, **kwargs):
        return value

    def number_input(self, label, value=0, **kwargs):
        return value

    def text_input(self, label, value="", **kwargs):
        return value

    def text_area(self, label, value="", **kwargs):
        return value

    def date_input(self, label, value=None, **kwargs):
        return value or date.today()

    def slider(self, label, min_value=None, max_value=None, value=None, **kwargs):
        if value is not None:
            return value
        return min_value

    def columns(self, specs):
        count = specs if isinstance(specs, int) else len(specs)
        return [FakeContext() for _ in range(count)]

    def tabs(self, labels):
        return tuple(FakeContext() for _ in labels)


class RepoStub:
    def __getattr__(self, name):
        return getattr(repository, name)

    @staticmethod
    def save_data(data):
        # Avoid file system writes during integration tests
        return None


class StreamlitPagesIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fake_st = FakeStreamlit()
        self.repo_stub = RepoStub()
        self.data = {
            "players": [
                {
                    "id": 1,
                    "name": "Alex",
                    "birth_year": 2016,
                    "preferred_position": "Milieu",
                    "foot": "Droit",
                    "base_ratings": {
                        "Passes courtes": 4,
                        "Passes longues": 3,
                        "Endurance": 5,
                    },
                },
                {
                    "id": 2,
                    "name": "Sam",
                    "birth_year": 2015,
                    "preferred_position": "Gardien",
                    "foot": "Gauche",
                    "base_ratings": {
                        "Passes courtes": 3,
                        "Contrôle orienté": 4,
                        "Placement": 5,
                    },
                },
            ],
            "matches": [
                {
                    "id": 10,
                    "date": date(2024, 4, 20).isoformat(),
                    "opponent": "Rivals FC",
                    "competition": "Amical",
                    "performances": [
                        {
                            "player_id": 1,
                            "position": "Milieu",
                            "minutes": 45,
                            "tech": 4,
                            "phys": 3,
                            "tact": 4,
                            "mental": 5,
                            "goals": 1,
                            "assists": 0,
                            "comment": "",
                        }
                    ],
                }
            ],
            "trainings": [
                {
                    "id": 7,
                    "date": date(2024, 4, 15).isoformat(),
                    "theme": "Conduite de balle",
                    "type": "Technique",
                    "notes": "Travail en ateliers",
                    "attendances": [
                        {
                            "player_id": 1,
                            "present": True,
                            "effort": 4,
                            "focus": 3,
                            "comment": "Bon investissement",
                        }
                    ],
                }
            ],
        }

    def _render_with_fake_streamlit(self, module, data):
        with mock.patch.object(module, "st", self.fake_st):
            module.render(self.repo_stub, data)

    def test_pages_render_without_exception(self):
        datasets = {
            "players": copy.deepcopy(self.data),
            "matches": copy.deepcopy(self.data),
            "trainings": copy.deepcopy(self.data),
            "profiles": copy.deepcopy(self.data),
            "exports": copy.deepcopy(self.data),
        }

        self._render_with_fake_streamlit(players, datasets["players"])
        self._render_with_fake_streamlit(matches, datasets["matches"])
        self._render_with_fake_streamlit(trainings, datasets["trainings"])
        self._render_with_fake_streamlit(profiles, datasets["profiles"])

        with mock.patch.object(exports, "st", self.fake_st), mock.patch.object(
            exports, "generate_player_pdf", return_value=b"PDF"
        ):
            exports.render(self.repo_stub, datasets["exports"])


if __name__ == "__main__":
    unittest.main()
