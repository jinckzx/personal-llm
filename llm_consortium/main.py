from llm_consortium.ui.app import create_ui
from llm_consortium.core.logging import configure_logging

configure_logging()
if __name__ == "__main__":
    ui = create_ui()
    ui.launch()