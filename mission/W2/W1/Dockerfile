FROM jupyter/base-notebook:python-3.11.6

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /home/jovyan/work

EXPOSE 8888

CMD ["start-notebook.py", "--NotebookApp.token=''"]