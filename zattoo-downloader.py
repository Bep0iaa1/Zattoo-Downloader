# Since this is in alpha, please report any bug or suggestions to improve this application
# Credits: krasny013, sunsettrack4
# Version 3.0a

import os
import subprocess
import time
import argparse
import requests
import uuid
import re
import threading
import getpass
import datetime
import math
import shutil
import platform
import zipfile
import sys

class Zattoo:
    def __init__(self, userData):
        while 'email' not in userData or not isinstance(userData['email'], str) or len(userData['email'].strip()) == 0 or '@' not in userData['email']:
            userData['email'] = input("Please enter the email address of your Zattoo account: ").strip()
        
        while 'password' not in userData or not isinstance(userData['password'], str) or len(userData['password'].strip()) == 0:
            userData['password'] = getpass.getpass("Please enter the password of your Zattoo account: ").strip()

        self.userData = userData
        self.lang = userData.get('lang', 'en')
        self.domain = userData.get('domain', 'zattoo.com')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Accept-Language': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'https://{self.domain}/client',
            'Origin': f'https://{self.domain}',
            'Host': self.domain
        })

    def checkFFmpeg(self):
        if os.path.exists("ffmpeg") == False:
            os.mkdir("ffmpeg")

        dest = os.path.abspath("ffmpeg")
        current_os = platform.system().lower()

        try:
            if current_os == 'darwin':
                ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode('utf-8').strip()
                ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode('utf-8').strip()

                if not ffmpeg_path:
                    subprocess.check_call(['brew', 'install', 'ffmpeg'])
                    ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode('utf-8').strip()
                    ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode('utf-8').strip()

            elif current_os == 'linux':
                ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode('utf-8').strip()
                ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode('utf-8').strip()

                if not ffmpeg_path:
                    if os.path.exists('/etc/apt/'):
                        subprocess.check_call(['sudo', 'apt', 'update'])
                        subprocess.check_call(['sudo', 'apt', 'install', '-y', 'ffmpeg'])
                    elif os.path.exists('/etc/yum/'):
                        subprocess.check_call(['sudo', 'yum', 'install', '-y', 'ffmpeg'])
                    elif os.path.exists('/etc/dnf/'):
                        subprocess.check_call(['sudo', 'dnf', 'install', '-y', 'ffmpeg'])
                    elif os.path.exists('/etc/pacman.conf'):
                        subprocess.check_call(['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'])
                    ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode('utf-8').strip()
                    ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode('utf-8').strip()

            if ffmpeg_path:
                shutil.copy(ffmpeg_path, dest)
                shutil.copy(ffprobe_path, dest)

            else:
                print("FFmpeg installation failed.")

        except Exception as e:
            print(f"Error: {e}")

    def checkFFmpegWindows(self):
        ffmpegDir = os.path.abspath("ffmpeg")
        zipFile = f"{ffmpegDir}/ffmpeg-release-essentials.zip"
        install = 0
        if not os.path.exists(ffmpegDir):
            print("ffmpeg folder not available!")
            install = 1
        else:
            if not os.path.exists(f"{ffmpegDir}/ffmpeg.exe"):
                print("ffmpeg not found!")
                install = 1

            if not os.path.exists(f"{ffmpegDir}/ffprobe.exe"):
                print("ffprobe not found!")
                install = 1

            if os.path.exists(zipFile):
                os.remove(zipFile)

        if install == 1:
            os.makedirs(ffmpegDir, exist_ok=True)
            print("Downloading ffmpeg, please wait...")
            response = requests.get("https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-essentials_build.zip")

            if response.status_code == 200:
                    with open(zipFile, 'wb') as file:
                        file.write(response.content)

                    if os.path.exists(zipFile):
                        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
                            zip_contents = zip_ref.namelist()
                            for folder in zip_contents:
                                if folder.startswith("ffmpeg-"):
                                    versioned_folder = folder.split('/')[0]
                                    break

                            for file in zip_contents:
                                if file.startswith(f"{versioned_folder}/bin/ff"):
                                    zip_ref.extract(file, ffmpegDir)
                                    shutil.move(f"{ffmpegDir}/{file}", f"{ffmpegDir}/{os.path.basename(file)}")
                            
                            for dir_name in os.listdir(ffmpegDir):
                                full_path = os.path.join(ffmpegDir, dir_name)

                                if os.path.isdir(full_path) and dir_name.startswith("ffmpeg-"):
                                    subprocess.run(f'rmdir /s /q "{full_path}"', shell=True)
                                    subprocess.Popen([sys.executable, os.path.abspath(__file__)] + sys.argv[1:])
                                    sys.exit()

    def get_app_token(self):
        res = self.session.get(f'https://{self.domain}/token.json')
        self.app_token = res.json().get('session_token')

    def get_session(self):
        uid = str(uuid.uuid4())
        self.session.cookies.set('uuid', uid, domain=self.domain)

        params = {
            'uuid': uid,
            'lang': self.lang,
            'format': 'json',
            'app_version': '3.2120.1',
            'client_app_token': self.app_token
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }

        res = self.session.post(f'https://{self.domain}/zapi/v3/session/hello', data=params, headers=headers)
        self.session_info = res.json()
        if not (self.session_info.get('active') or self.session_info.get('success')):
            raise Exception('hello failed')

    def get_login(self):
        params = {
            'login': self.userData['email'],
            'password': self.userData['password'],
            'remember': 'true',
            'format': 'json'
        }
        res = self.session.post(f'https://{self.domain}/zapi/v3/account/login', data=params)
        if not res.json().get('active'):
            raise Exception('login failed')
    
    def get_recording_library(self):
        res = self.session.get(f'https://{self.domain}/zapi/v2/playlist')
        return res.json()
    
    def get_recordings_default(self, power_guide_hash, page, perPage):
        res = self.session.get(f'https://{self.domain}/zapi/v2/cached/{power_guide_hash}/teaser_collections/ptc_recordings_all_recordings?page={page}&per_page={perPage}')
        res2 = res.json()

        return res2
    
    def get_allrecordings(self, power_guide_hash):
        perPage = 30

        recording_library = self.get_recording_library().get("recordings", [])
        recordings_default = self.get_recordings_default(power_guide_hash, 0, perPage)
        maxPage = recordings_default.get("teasers_total")

        library_program_map = {}
        for rec in recording_library:
            program_id = rec["program_id"]
            if program_id not in library_program_map:
                library_program_map[program_id] = []
            library_program_map[program_id].append(rec["id"])

        matching_recordings = []
        recordingIndex = 0

        def process_page(pages):
            nonlocal recordingIndex
            recordings_get = self.get_recordings_default(power_guide_hash, pages, perPage)
            recordings_page = recordings_get.get("teasers")

            for rec in recordings_page:
                teasable_id = rec.get("teasable_id")
                if teasable_id in library_program_map:
                    channel_name = rec.get("teasable", {}).get("channel_name")

                    serie_no=rec.get("teasable", {}).get("s_no")
                    if serie_no == None or serie_no == 0:
                        serie_no = ""
                    else:
                        serie_no = f"S{serie_no:02d}"

                    episode_no = rec.get("teasable", {}).get("e_no")
                    if episode_no == None or episode_no == 0:
                        episode_no = ""
                    else:
                        episode_no = f"E{episode_no:02d}"

                    episode = rec.get("text") or ""
                    year=rec.get("teasable", {}).get("year")
                    country=rec.get("teasable", {}).get("country")
                    classif=rec.get("teasable", {}).get("c") or ""
                    genre=rec.get("teasable", {}).get("g") or ""
                    picture_url=rec.get("teasable", {}).get("i_url")

                    for library_id in library_program_map[teasable_id]:
                        recordingIndex += 1
                        matching_recordings.append({
                            "recordingIndex": recordingIndex,
                            "program_id": teasable_id,
                            "library_id": library_id,
                            "title": rec.get("title"),
                            "episode": episode,
                            "channel": channel_name,
                            "serie": serie_no,
                            "epis": episode_no,
                            "year": year,
                            "country": country,
                            "class": classif,
                            "genre": genre,
                            "picture": picture_url
                        })
            return "OK"

        page = 0

        while maxPage > len(matching_recordings):
            time.sleep(1)
            #print(f"page: {page}, matching_recordings: {len(matching_recordings)}, maxPage: {maxPage}") This is only good for debugging
            check = process_page(page)
            while check != "OK":
                time.sleep(1)
            page += 1

        return matching_recordings

    def getSessionInfo(self):
        self.get_app_token()
        self.get_session()
        self.get_login()
        return self.session_info
    
    def playlistSelectMenu(self, recordings):
        while True:
            os.system('cls' if os.name == "nt" else 'clear')
            print("\nAvailable recordings:\n")
            for recording in recordings:
                episodes = ""
                if recording['episode'] is not None and recording['episode'] != "":
                    episodes = f"- {recording['episode']} ({recording['serie']}{recording['epis']}) "

                print(f"{recording['recordingIndex']}. {recording['title']} {episodes}[{recording['channel']}] ({recording['year']}, {recording['country']}, {''.join(recording['class']).replace(']', '')}, {''.join(recording['genre']).replace('[', '')})")

            try:
                selectedRecs = input(f"\nFor example: 1,2,3....\nAdd recordings to your list: ")
                if ("," in selectedRecs and selectedRecs.replace(",", "").isdigit() and all(1 <= int(x) <= len(recordings) for x in selectedRecs.split(","))):
                    return selectedRecs
                if "," not in selectedRecs and selectedRecs.isdigit():
                    if 1 <= int(selectedRecs) <= len(recordings):
                        selected_recording = recordings[int(selectedRecs) - 1]
                        return selected_recording
                    else:
                        print(f"Invalid input!\nPlease choose a number between 1 and {len(recordings)}.")
                        time.sleep(2)
                        continue
                else:
                    print(f"Invalid input!\nPlease choose a number between 1 and {len(recordings)}.")
                    time.sleep(2)
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)
                continue
    
    def selectRecording(self, recordings, downloadProc):
        while True:
            os.system('cls' if os.name == "nt" else 'clear')
            if "ERR" in downloadProc:
                if "0" in downloadProc:
                    print("Error: Download wasn't successful\n")
                if "-2" in downloadProc:
                    print("Error: Requested file isn't available\n")

            if not recordings:
                print("No recordings available to select.")
                return None

            print("\nAvailable recordings:\n")
            episodes = ""
            for recording in recordings:
                if recording['episode'] is not None and recording['episode'] != "":
                    episodes = f"- {recording['episode']} ({recording['serie']}{recording['epis']}) "

                print(f"{recording['recordingIndex']}. {recording['title']} {episodes}[{recording['channel']}] ({recording['year']}, {recording['country']}, {''.join(recording['class']).replace(']', '')}, {''.join(recording['genre']).replace('[', '')})")
            try:
                selected_index = input(f"\nWhich recording do you want to download? (1-{len(recordings)})\nPress 'L' to create a downloadlist: ")
                if selected_index == "L" or selected_index == "l":
                    return "L"
                elif 1 <= int(selected_index) <= len(recordings):
                    selected_recording = recordings[int(selected_index) - 1]
                    return selected_recording
                else:
                    print(f"Invalid input!\nPlease choose a number between 1 and {len(recordings)}.")
                time.sleep(2)
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)
        
    def modifyM3U8(self, input_data, Channel, token, low, domain):
        output = "#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-INDEPENDENT-SEGMENTS\n"
        
        audio_pattern = re.compile(r'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="([^"]+)",NAME="([^"]+)",DEFAULT=([^,]+),AUTOSELECT=([^,]+),LANGUAGE="([^"]+)"')
        audio_matches = audio_pattern.findall(input_data)

        nd = re.search(r'nd_(\d+)', input_data)
        frameRate = re.search(r'FRAME-RATE=(\d+)', input_data)
        
        languages = {}
        
        for match in audio_matches:
            group_id, name, default, autoselect, language = match
            if language not in languages:
                languages[language] = []
            languages[language].append((name, default == "YES"))
        
        #uri = f"https://{domain}-pvr.zahs.tv/{Channel}"
        uri = f"https://fr5-v6-5-hls7-pvr.zahs.tv/{Channel}"

        if low == 1:
            res = "768x432"
            quality = 1500
        elif low == 0:
            res = "1920x1080"
            quality = 8000
        
        output += f"#EXT-X-STREAM-INF:BANDWIDTH={quality}000,CODECS=\"avc1.4d401e,mp4a.40.2\",RESOLUTION={res},FRAME-RATE={frameRate.group(1)},AUDIO=\"audio\",CLOSED-CAPTIONS=NONE\n"
        output += f"{uri}/t_track_video_bw_{quality - 200}000_num_0_tid_1_nd_{nd.group(1)}_mbr_{quality}.m3u8?z32={token}\n"
        
        for language, audio_tracks in languages.items():
            for name, is_default in audio_tracks:
                audio_uri = f"{uri}/t_track_audio_bw_128000000_num_0_tid_2_p_10_l_{language}_nd_{nd.group(1)}_mbr_{quality}.m3u8?z32={token}"
                output += f"#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"audio\",NAME=\"{name}\",DEFAULT={'YES' if is_default else 'NO'},AUTOSELECT=YES,LANGUAGE=\"{language}\",URI=\"{audio_uri}\"\n"
        
        return output
    
    def get_video_infs(self, file_path):
        global normalProc
        try:
            if os.name == "nt":
                ffprobeExe = "ffprobe.exe"
            else:
                ffprobeExe = "ffprobe"

            info = {}
            result = subprocess.Popen(
                [os.path.join(os.path.abspath("ffmpeg"), ffprobeExe), file_path, 
                 "-protocol_whitelist", "file,http,https,tcp,tls,crypto", 
                 "-show_entries", "format=duration", "-show_streams", "-select_streams", "v", "-pretty"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.path.abspath("ffmpeg")
            )

            stdout, stderr = result.communicate()

            while "bit_rate=" not in stdout:
                print(f"Loading file")
                if "duration=N/A" in stdout:
                    time.sleep(2000)
                    normalProc = -1 
                    break

            bitrate_match = re.search(r'bit_rate=([\d.]+)', stdout)
            if bitrate_match:
                info['bitrate'] = float(bitrate_match.group(1)) / 1_000_000

            duration_match = re.search(r'duration=(\d{1,2}):(\d{2}):(\d{2}\.\d+)', stdout)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                time_obj = datetime.datetime.strptime(f"{hours}:{minutes}:{seconds}", "%H:%M:%S.%f")
                total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1e6
                info['duration'] = total_seconds

            if not duration_match:
                duration_seconds_match = re.search(r'duration=([\d.]+)', stdout)
                if duration_seconds_match:
                    info['duration'] = float(duration_seconds_match.group(1))

            return info

        except Exception as e:
                print(f"Error extracting video info: {e}")
                return None
    
    def downloadSelectedRecording(self, selectedRecording, low):
        global normalProc
        normalProc = 0

        if selectedRecording:
            params = {
                "with_schedule": False,
                "stream_type": "hls7",
                "https_watch_urls": True,
                "sdh_subtitles": True
            }
            print(f"\nPreparing download")

            try:
                hls7res = self.session.post(f'https://{self.domain}/zapi/watch/recording/{selectedRecording["library_id"]}', params=params)
                res = hls7res.json()

                streams = res.get("stream")
                if not streams:
                    print("No streams found.")
                    return
                
                quality = streams.get("quality").upper()
                if quality == "HD":
                    low = 0
                else:
                    low = 1

                episodes = ""
                if selectedRecording['episode'] is not None and selectedRecording['episode'] != "":
                    episodes = f"- {selectedRecording['episode']} ({selectedRecording['serie']}{selectedRecording['epis']}) "

                channel = "".join(selectedRecording['channel']).replace("HD", quality)
                title = f"{selectedRecording['recordingIndex']}. {selectedRecording['title']} {episodes}[{channel}] ({selectedRecording['year']}, {selectedRecording['country']}, {''.join(selectedRecording['class']).replace(']', '')}, {''.join(selectedRecording['genre']).replace('[', '')})"
                
                title = title.replace('\'', "")
                title = title.replace("?", "")
                title = title.replace(":", "")
                title = title.replace(">", "")
                title = title.replace("<", "")
                title = title.replace("|", "")
                title = title.replace("*", "")
                title = title.replace("/", " ")
                title = title.replace("\\", "")
                title = title.replace('"', "")
                
                tmp = os.path.abspath("tmp")
                ffmpegDir = os.path.abspath("ffmpeg")
                titlePath = os.path.abspath(f"{tmp}/{title}.m3u8")
                outputPath = os.path.abspath(f"output/{title}.mp4")

                if os.path.exists(outputPath):
                    inputPath = input("File already exists! Do you still want to download it? (y/n)\n")
                    if inputPath == "y" or inputPath == "yes":
                        counter = 1
                        while True:
                            new_outputPath = os.path.abspath(f"output/{title} ({counter}).mp4")
                            if not os.path.exists(new_outputPath):
                                outputPath = new_outputPath
                                break
                            counter += 1
                    else:
                        return "abr"

                if os.name == "nt":
                    ffmpegExe = "ffmpeg.exe"
                else:
                    ffmpegExe = "ffmpeg"

                watchurl = streams.get("watch_urls")
                url_map = []

                for urls in watchurl:
                    urlMain = urls["url"]
                    if urlMain not in url_map:
                        url_map.append(urlMain)
                    break

                url_string = ''.join(url_map)
                url_pattern = r'https://(.*?)pvr\.zahs\.tv/(.*?)/m.m3u8'
                match = re.search(url_pattern, url_string)
                token_pattern = r'z32=([^&]+)'

                getm3u8 = requests.get(url_string)
                token_match = re.search(token_pattern, url_string)
                finalm3u8 = self.modifyM3U8(getm3u8.text, match.group(2), token_match.group(1), low, match.group(1))

                if not os.path.exists("tmp"):
                    os.makedirs("tmp")

                with open(f"{titlePath}", "w") as file:
                    file.write(finalm3u8)

                video_perfs = self.get_video_infs(titlePath)
                duration = video_perfs.get('duration')
                bitrate = video_perfs.get('bitrate')

                if not os.path.exists("output"):
                    os.makedirs("output")
                
                if os.name == "nt":
                    process = subprocess.Popen(
                        [os.path.join(ffmpegDir, ffmpegExe), "-protocol_whitelist", "file,http,https,tcp,tls,crypto", "-i", titlePath, "-map", "0", "-c", "copy", outputPath],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        cwd=ffmpegDir
                    )
                else: 
                    process = subprocess.Popen(
                        [os.path.join(ffmpegDir, ffmpegExe), "-protocol_whitelist", "file,http,https,tcp,tls,crypto", "-i", titlePath, "-map", "0", "-c", "copy", outputPath],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=ffmpegDir
                    )

                def track_progress():
                    global normalProc

                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    seconds = int(duration % 60)
                    
                    start_time = time.time()
                    video_duration = f"{hours:02}:{minutes:02}:{seconds:02}"
                    reset = True
                    firstSizeActive = 1

                    while True:
                        line = process.stderr.readline()
                        if "duration=N/A" in line:
                            if low == 0:
                                normalProc = -1
                            elif low == 1:
                                normalProc = -2

                            process.terminate() 
                            break
                        
                        if reset == True:
                            os.system('cls' if os.name == "nt" else 'clear')
                            print(f"\nDownloading: {selectedRecording['recordingIndex']}. {selectedRecording['title']} - {selectedRecording['episode']} ({channel}), ID: {selectedRecording['library_id']})\nDownload Location: {outputPath}\n")
                            reset = False
                        if not line:
                            break
                        
                        if "time=" in line:
                            time_info = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                            
                            if time_info:
                                current_time = time_info.group(1)
                                try:
                                    current_seconds = sum(x * float(t) for x, t in zip([3600, 60, 1], current_time.split(":")))
                                    total_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], video_duration.split(":")))
                                    progress_percentage = (current_seconds / total_seconds) * 100

                                    elapsed_seconds = time.time() - start_time
                                    estimated_total_time = elapsed_seconds / (progress_percentage / 100) if progress_percentage > 0 else 0
                                    remaining_seconds = max(estimated_total_time - elapsed_seconds, 0)

                                    elapsed_h = int(elapsed_seconds // 3600)
                                    elapsed_m = int((elapsed_seconds % 3600) // 60)
                                    elapsed_s = int(elapsed_seconds % 60)

                                    remaining_h = int(remaining_seconds // 3600)
                                    remaining_m = int((remaining_seconds % 3600) // 60)
                                    remaining_s = int(remaining_seconds % 60)

                                    if firstSizeActive == 1:
                                        file_size_bytes = (bitrate * 1_000_000 * duration) / 8
                                        file_size_mb = file_size_bytes / (1024 * 1024)
                                        firstSize = file_size_mb * 1000000

                                        # Scales down if ffprobe gives ridiculous size
                                        if firstSize > 102400:
                                            firstSize = firstSize / 100

                                        firstSizeActive = 0
                                        
                                    print(f"Progress: {progress_percentage:.2f}% ({os.path.getsize(outputPath) / (1024**2):.2f} MB / {firstSize:.2f} MB (≈ {firstSize / 1024:.1f} GB) | Elapsed: {elapsed_h:02}:{elapsed_m:02}:{elapsed_s:02} | Remaining: {remaining_h:02}:{remaining_m:02}:{remaining_s:02})", end="\r")

                                except ValueError:
                                    print(f"Error converting time: {current_time}")

                if normalProc == 0:
                    if low == 1:
                        low = 0

                    # start a separate thread to avoid blocking
                    progress_thread = threading.Thread(target=track_progress)
                    progress_thread.start()

                    process.wait()
                    progress_thread.join()

                    print(f"Progress: 100%   ", end="\r")
                    print("\nDownload completed.")
                    return outputPath

                elif normalProc == -1:
                    low = 1
                    self.downloadSelectedRecording(selectedRecording, 1)
                elif normalProc == -2:
                    print("Error: Requested file isn't available")
                    return "ERR-2"
                
                os.system(f"rmdir /s /q {tmp}" if os.name == "nt" else f"rm -rf {tmp}")

                return "OK"
            except Exception as e:
                print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    def proc(session_info, downloadProc):
        while True:
            recordings = zattoo.get_allrecordings(session_info.get("power_guide_hash"))
            srResult = zattoo.selectRecording(recordings, downloadProc)

            if srResult == "L" or srResult == "l":
                outputPath = None
                playlistSelected = zattoo.playlistSelectMenu(recordings)
                # print(f"Selected: {playlistSelected}")

                downloadList = playlistSelected.split(',')

                for index in downloadList:
                    index = index.strip()

                    if index.isdigit():
                        recording = None
                        for rec in recordings:
                            if rec.get('recordingIndex') == int(index):
                                recording = rec
                                break

                        print(f"Next: {index}. {recording.get('title')} - {recording.get('episode')}")
                        downloadProc = zattoo.downloadSelectedRecording(recording, 0)
                        if downloadProc in ("OK", "abr"):
                            downloadProc = "OK"
                        elif "ERR" in downloadProc:
                            continue
                        else:
                            outputPath = downloadProc
                    else:
                        continue

                print("All downloads completed!")
                if os.name == "nt":
                    subprocess.run(['explorer', '/select,', outputPath])
                else:
                    subprocess.run(['open', os.path.dirname(outputPath)])
                time.sleep(1)
                continue

            downloadProc = zattoo.downloadSelectedRecording(srResult, 0)
            if downloadProc in ("OK", "abr"):
                downloadProc = "OK"
            elif "ERR" in downloadProc:
                continue
            else:
                if os.name == "nt":
                    subprocess.run(['explorer', '/select,', downloadProc])
                else:
                    subprocess.run(['open', os.path.dirname(downloadProc)])

    os.system('cls' if os.name == "nt" else 'clear')
    parser = argparse.ArgumentParser(description="Zattoo Recording Library Downloader")
    parser.add_argument('--Email', required=False, help="Zattoo Email")
    parser.add_argument('--Password', required=False, help="Zattoo Password")

    args = parser.parse_args()

    userData = {
        'email': args.Email,
        'password': args.Password
    }

    zattoo = Zattoo(userData)
    if  os.name == 'nt':
        zattoo.checkFFmpegWindows()
    else:
        zattoo.checkFFmpeg()

    tmp = os.path.abspath("tmp")
    if os.path.exists(tmp):
        os.system(f"rmdir /s /q {tmp}" if os.name == "nt" else f"rm -rf {tmp}")

    session_info = zattoo.getSessionInfo()
    print("Gathering Information, Please Wait!")
    proc(session_info, "")
