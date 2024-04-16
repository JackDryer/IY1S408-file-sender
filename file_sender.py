""" A simple flask app that can send and receive over http or https
Serves the contents of the current directory

Usage: python file_sender.py -p port (default  8080) -r folder_to_receive_files_to (default /received_files) -s (use https) -y (dont ask for validation before receiving a file)
equivalent to: python file_sender.py --port 8080 --receive_folder --https --accept_all_files

"""
import logging
from pathlib import Path
from typing import List, Iterable, Literal, Tuple
from flask import Flask, send_from_directory, request, redirect, url_for
from werkzeug.utils import safe_join, secure_filename
import os

app: Flask = Flask(__name__)
log = logging.getLogger('werkzeug')

DIR_PATH: Path = Path.cwd()

toflash: List[str] = []  # how to avoid template injection, dont use templates,
# however this should never contain user input due to xss


def get_flash() -> str:
    """returns any messages that need to be flashed 
    to allow messages to be comminuted back to the user
    this is an imitation of flasks in built flash() without templates"""
    temp = ""
    while toflash:
        temp += toflash.pop()
    return temp


upload_form = """
<form method=post action="/upload" enctype=multipart/form-data>
      <input type=file name=file id=fileholder>
      <input type=submit value=Upload>
    </form>

    """


def get_files_from_directory(path :str) -> Iterable[Tuple[Literal["file","dir"], str]]:
    """returns all a generator for every file and folder in the provided path 
    along with whether it is a file or folder
    
    path must be a subdiretory of the current working directory for safety reasons""" 
    path = Path(safe_join(DIR_PATH, path))
    for dir_item in path.iterdir():
        if dir_item.is_file():
            yield "file", dir_item.name
        elif dir_item.is_dir():
            yield "dir", dir_item.name
        else:
            raise FileExistsError


@app.route("/files/<path:file_name>")  # type: ignore
def serve_file(file_name: str) -> str:
    """safely serves a file if its in the current directory"""
    return send_from_directory(DIR_PATH, file_name)


def html_ul_of_items(path: str) -> str:
    """returns HTML to access all the items in the provides path"""
    html: str = "<ul>"
    for item_type, dir_item in get_files_from_directory(path):
        if item_type == "file":
            html += f"""<li><a href='/files/{path}/{
                dir_item}'>{dir_item}</a></li>"""
        if item_type == "dir":
            html += f"""<li><a href='/explore/{path}/{
                dir_item}'>{dir_item}</a></li>"""
    return f"{html}</ul>"


@app.route("/")  # type: ignore
def serve_index() -> str:
    """serve the root directory (being the current working directory)"""
    log.setLevel(logging.ERROR) # dont log every get requests, but print the port and ip first
    return html_ul_of_items("")+upload_form + get_flash()


@app.route("/explore/")
@app.route("/explore")
def redirect_to_main() -> str:
    """redirects to the root directory"""
    return redirect("/")


@app.route("/explore/<path:folder_path>")
def serve_path(folder_path: str) -> str:
    """provides a view of the contents of a folder provided by path"""
    return html_ul_of_items(folder_path) + upload_form + get_flash()


@app.route('/upload', methods=['POST'])
def upload_file()-> str:
    """receives an uploaded file and saves it if the user allows it 
    or the server it set to accept all files"""
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
            if not app.config["accept_all_files"]:
                choice = input(f'''A user wants to send a file "{
                           filename}" Accept? y/\u0332N''') # \u0332 is used to underline the no option
            else:
                choice = "y"
            if choice.lower() == "y":
                file.save(filepath)
                print(f"Saving to {filepath}")
                toflash.append("File uploaded successfully")
            else:
                toflash.append("File rejected")
            return redirect(request.host_url)


def main() -> None:
    """Run the flask app."""
    import argparse
    parser = argparse.ArgumentParser(prog='File Sender',
                                     description='Sends and receives files form the current working directory')
    parser.add_argument("-p", '--port', nargs=1, default=8080, type=int)
    parser.add_argument("-r", '--receive_folder', nargs=1,
                        default="received_files/", type=str)
    parser.add_argument("-s", '--https', action='store_true')
    parser.add_argument("-y", '--accept_all_files', action='store_true')
    args = parser.parse_args()
    port = args.port[0] if isinstance(args.port, list) else args.port
    UPLOAD_FOLDER: str = args.receive_folder[0] if isinstance(
        args.receive_folder, list) else args.receive_folder
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config["accept_all_files"] = args.accept_all_files
    if not Path(UPLOAD_FOLDER).exists():
        Path(UPLOAD_FOLDER).mkdir()
    from socket import gethostname
    print(f"hostname: {gethostname()}")
    if args.https:
        app.run(host='0.0.0.0', port=port,ssl_context='adhoc')
    else:
        app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    main()
