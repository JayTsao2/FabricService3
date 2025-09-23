import os
import shutil
from git import Repo


repo_path = "config_temp"
repo_url = "https://github.com/Elwing-Chou/precommit_demo.git"

# Clone if it doesn't exist, otherwise load
try:
    repo = Repo(repo_path)
except:
    repo = Repo.clone_from(repo_url, repo_path)

git = repo.git
git.checkout('main')
# checkout commit
# git.checkout('abcdef12345')


source_directory = './config_temp/network_configs'
destination_directory = './network_configs' # Replace with your destination directory path

try:
    if os.path.exists(destination_directory):
        shutil.rmtree(destination_directory)
    shutil.copytree(source_directory, destination_directory)
    print(f"Directory '{source_directory}' successfully copied to '{destination_directory}'")
except FileExistsError:
    print(f"Error: Destination directory '{destination_directory}' already exists.")
