from pathlib import Path
from typing import List
from flask import Flask, send_from_directory, request, redirect, url_for
from werkzeug.utils import safe_join, secure_filename
import os

app: Flask = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
UPLOAD_FOLDER = 'received_files/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DIR_PATH: Path = Path(__file__).parent

toflash :List[str] = [] # how to avoid template injection, dont use templates, 
#however this should never contain user input due to xss
def get_flash() ->str:
    temp = ""
    while toflash:
        temp+= toflash.pop()
    return temp

upload_form =   """
<form method=post action="/upload" enctype=multipart/form-data>
      <input type=file name=file id=fileholder>
      <input type=submit value=Upload>
    </form>

    """

def get_files_from_directory(path):
    path = Path(safe_join(DIR_PATH,path))
    for dir_item in path.iterdir():
        if dir_item.is_file():
            yield "file", dir_item.name
        elif dir_item.is_dir():
            yield "dir", dir_item.name
        else:
            raise FileExistsError

@app.route("/files/<path:file_name>")  # type: ignore
def serve_file(file_name: str):
    return send_from_directory(DIR_PATH, file_name)


def html_ul_of_items(path:str) -> str:
    html: str = "<ul>"
    for item_type, dir_item in get_files_from_directory(path):
        if item_type == "file":
            html += f"<li><a href='/files/{path}/{dir_item}'>{dir_item}</a></li>"
        if item_type == "dir":
            html += f"<li><a href='/explore/{path}/{dir_item}'>{dir_item}</a></li>"
    return f"{html}</ul>"


@app.route("/")  # type: ignore
def serve_index() -> str:
    log.setLevel(logging.ERROR) 
    return  html_ul_of_items("")+upload_form+ get_flash()

@app.route("/explore/")
@app.route("/explore") 
def redirect_to_main() -> str:
    return redirect("/")
@app.route("/explore/<path:folder_path>") 
def serve_path(folder_path: str) -> str:
    return html_ul_of_items(folder_path) +upload_form + get_flash()

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            toflash.append('No file part')
            return redirect(request.host_url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            toflash.append('No selected file')
            return redirect(request.host_url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            choice = input (f'A user wants to send a file "{filename}" Accept? y/\u0332N')
            if choice.lower() == "y":
                file.save(filepath)
                print (f"Saving to {filepath}")
                toflash.append("File uploaded successfully")
            else:
                toflash.append("File rejected")
            return redirect(request.host_url)
def main() -> None:
    """Run the flask app."""
    import sys
    
    match len(sys.argv):
        case 1:
            port = 8080
        case 2:
            port = sys.argv[1]
        case _:
            print("too many command line arguments")
            return
    app.run(host='0.0.0.0',port=port)


if __name__ == "__main__":
    main()