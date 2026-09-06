README.txt

6th September 2026
UI finally added, only appNew.py is required for running the application. No other files. If you are copying this file locally, then the command variable needs to be set according to your preferred storage location, example would be 
export DATA_ROOT_DIR="/home/your_username/Downloads/yourfolder". Then pip install the required packages and then run using: python appNew.py 

N.B. the UI is in Gradio so I have deleted the streamlit files that I was using for testing a possible UI because I found gradio to be really good instead. 

N.B. 2. a working (temporary) public link can be supplied by contacting me at chriscomptonwork (at) proton.me

3rd September 2026
This public MultiAgentWorkflow_RAG repository is a small subset of a bigger private repository that has a Docker image built in Codespaces. That Codespaces project has a full end-2-end version of this same RAG, but due to lack of disc space, the Docker image calls out to Ollama that is hosted on my local machine, rather than being directly hosted in the Docker image. That Codespace is available to demo on request.

This public repository, is an adaptation of the main python file appNew.py.
The adaptation goes beyond the original proof of concept and introduces more Production ready quality, and in addition a UI (work in progress) using streamlit. At the moment any additional files (beyond appNew.py) are for testing and development of the UI. 

Thanks for looking.
