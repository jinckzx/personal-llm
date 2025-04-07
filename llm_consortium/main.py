# from llm_consortium.gradio_ui.app import create_ui
# from llm_consortium.utils.logging import configure_logging

# configure_logging()
# if __name__ == "__main__":
#     ui = create_ui()
#     ui.launch()
"""above code is for gradio ui"""
import subprocess
from llm_consortium.utils.logging import configure_logging

configure_logging()

if __name__ == "__main__":
    # Adjust the path to app.py if necessary.
    subprocess.run(["streamlit", "run", "D:/inforigin_projects/personal-llm/llm_consortium/streamlit_ui/app.py"])
