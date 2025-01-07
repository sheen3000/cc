# -*- coding: utf-8 -*-
"""
Created on Thu May 30 19:35:39 2024

@author: shawn
"""

import os
from pathlib import Path
from elevate import elevate

# Elevate the script to run as an administrator
#elevate(show_console=False)

# Parameters
#base_path = Path('C:/users/shawn/credit-cards-shawn/data/') # "Credit card Agreement database"
    
#os.chdir('C:/users/shawn/credit-cards-shawn/data/')

# with open('.upcase_files_folders.log', 'a') as logfile:
#     renames=[]
#     for d, subdirs, fs in os.walk(os.getcwd()):
#         for x in fs + subdirs:
#             oldname = os.path.join(d,x)
#             newname = os.path.join(d, x.upper())
#             if newname == oldname:
#                 continue
#     for (oldname, newname) in reversed(renames):
#         os.rename(oldname, newname)
#         print("renamed: %s --> %s" %  (repr(oldname), repr(newname)), file=logfile)
# def get_perm(fname):
#     return stat.S_IMODE(os.lstat(fname)[stat.ST_MODE])
   
# def make_writeable_recursive(path):
#     for root, dirs, files in os.walk(path, topdown=False):
#         for dir in [os.path.join(root, d) for d in dirs]:
#             os.chmod(dir, get_perm(dir) | stat.S_IWRITE)
#         for file in [os.path.join(root, f) for f in files]:
#             os.chmod(file, get_perm(file) | stat.S_IWRITE)
            
# make_writeable_recursive('C:/users/shawn/credit-cards-shawn/data/')        


def capitalize_sub_folders(root_directory):
    for root, dirs, files in os.walk(root_directory, topdown=False):
        for dir_name in dirs:
            current_path = os.path.join(root, dir_name)
            capitalized_name = dir_name.capitalize()
            new_path = os.path.join(root, capitalized_name)
            os.rename(current_path, new_path)

# Example usage:
root_directory = 'C:/users/shawn/credit-cards-shawn/data/'
capitalize_sub_folders(root_directory)

print("Capitalization of sub-folders is complete.")






