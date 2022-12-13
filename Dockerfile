FROM python:3.11-slim
RUN apt update && apt upgrade -y && apt autoremove -y
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
WORKDIR app/
COPY . .
EXPOSE 8000
CMD streamlit run app.py --server.port 8000 --server.address '0.0.0.0'
