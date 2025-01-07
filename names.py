'''
Script that processes credit card disclosure files
<FILL THIS>


TODO:

- Carefully weight costs of GPT4o and GPT3.5t
- Consider trimming at a max. number of pages (line 89 of readers.py currently sets that at 50 pages)
- ...
- ...

'''




# def get_zipped_subfolders_in_directory(base_directory):
#     zipped_subfolders = {}
    
#     # Iterate over files in the base directory
#     for entry in os.listdir(base_directory):
#         entry_path = os.path.join(base_directory, entry)
        
#         # Check if the entry is a ZIP file
#         if os.path.isfile(entry_path) and entry_path.endswith('.zip'):
#             with zipfile.ZipFile(entry_path, 'r') as zip_ref:
#                 subfolders = [
#                     name for name in zip_ref.namelist() if name.endswith('/')
#                 ]
#                 zipped_subfolders[entry] = subfolders

#     return zipped_subfolders

# # Example usage
# base_directory = Path('C:/users/shawn/credit-cards-shawn/data/')

# zipped_subfolders = get_zipped_subfolders_in_directory(base_directory)
# #for zip_file, subfolders in zipped_sub
# print(zipped_subfolders)




from pathlib import Path
import pandas as pd
import zipfile
import os
from collections import Counter




# Parameters
base_path = Path('C:/users/shawn/credit-cards-shawn/data/') # "Credit card Agreement database"
    
directory_list = list()
#Get a list of names of all subfolders that start with the character "2"
subfolder_names = [f.name for f in base_path.iterdir() if f.is_dir() and f.name.startswith('2')]
#subfolder_names = [x.upper() for x in subfolder_names]

for name in subfolder_names:
    
    directory_list.append(os.path.join(base_path, name))
    
print (directory_list)

#Print the list of subfolder names
# for name in subfolder_names:
#     print(name)
    
# # Example list of folder names

# for name in subfolder_names:
    
#     bank_names = [f.name for f in name.iterdir()]
#     print(bank_names)
    

def tally_sub_folders(folder_list):
    sub_folder_tally = {}

    for folder in folder_list:
        for root, dirs, files in os.walk(folder):
            for sub_folder in dirs:
                if sub_folder in sub_folder_tally:
                    sub_folder_tally[sub_folder] += 1
                else:
                    sub_folder_tally[sub_folder] = 1
    
    return sub_folder_tally

# Example usage:
#folder_list = ['/path/to/folder1', '/path/to/folder2']
tally = tally_sub_folders(directory_list)
print(tally)

df=pd.DataFrame(list(tally.items()), columns=['name', 'n'])
df.to_csv('../output/bank_count.tsv', sep='\t', index=False)


# copy

#df2=df[df['n']>23][:50]
#df2.to_csv('../output/bank_sample.tsv', sep='\t', index=False)


# ```    
    
# # Create a counter object to count occurrences
# counter=Counter()

# # Use a loop to count occurrences

# for name in subfolder_names:
#     counter[name] +=1
    
# # Print the counts

# for name, count in counter.items():
#     print(f"{name}: {count}")    


# # Convert the Counter object to a DataFrame

# df=pd.DataFrame(list(counter.items()), columns=['name', 'n'])

# # Save the DataFrame as a tab-separated file 

# df.to_csv('output.tsv', sep='\t', index=False)


    

   



