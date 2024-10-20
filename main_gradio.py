from config import Settings, get_settings
from agents.ansari import Ansari
from presenters.gradio_presenter import GradioPresenter

if __name__ == "__main__":
    agent = Ansari(get_settings())
    presenter = GradioPresenter(
        agent,
        app_name="Ansari",
        favicon_path="./favicon.ico",
    )
    presenter.present()
