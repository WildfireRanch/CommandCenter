# Baseimage
FROM python:3.12.10-slim-bookworm

# Update Packages
RUN apt update
RUN apt upgrade -y
RUN pip install --upgrade pip
# install git
RUN apt-get install build-essential -y


RUN mkdir /CrewAI-Studio

# Install requirements
COPY ./requirements.txt /CrewAI-Studio/requirements.txt
WORKDIR /CrewAI-Studio
RUN pip install -r requirements.txt

# Copy CrewAI-Studio
COPY ./ /CrewAI-Studio/

# Run app using our start.sh script
CMD ["bash", "start.sh"]
EXPOSE 8080
