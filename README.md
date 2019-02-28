# Audio Split line by line
(should be ready to use Google Speech Recognition API)

### 0. Prepare Google API 

    gcloud auth login
    
### 1. Prepare data and directory
Make a directory for the audio 
    
    mkdir ./{title} ./{title}/audio ./{title}/pre_audio

change the name of files and locate them in the directory above (./{title})

    - original text file: {title}_ORIGINAL.txt
      (eg. androcles-shorter_ORIGINAL.txt)
    
    - original audio file: {title}.mp3  
      (eg. androcles-shorter.mp3)
  
### 2. Change ROOT in main.py
***Title above and the ROOT below should be the same***

    ROOT = "title"

### 3. Run main.py
    python main.py
    
Final audio files will be created in audio directory

### Caution
* This code cannot make sentence audio files perfectly. (about maximum 85% can be processed)

* Success rate can be dramatically lower if the audio file has more sentences than that of the text file.

* Add . after the title of the text if there is any. (To split sentences correctly)

* If you want to observe the analyzing process, change DEBUG in each python file to 1 (Currently 0)
____________________________________________________
### Future Work
* Solve the problem of having two candidate indices
  (eg. when 'me' appears twice in a sentence)
  
* Add a function to check the unknown chunks depending on its number

* Add a function to update once more with the way of increasing the index of chunk, rather than sentence number

* Process Bar (tqdm)

* Add docopt
