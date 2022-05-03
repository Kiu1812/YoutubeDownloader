## Import all necessary modules
from threading import Lock, Event, Thread
from os import getcwd
import subprocess
from time import sleep
from asyncio import run as async_run, get_event_loop as async_get_event_loop
from websockets import serve as websocket_serve
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image
import os
import sys

import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedg


# I don't know from who I copied this code.
# But if you're the creator tell me and I'll put you here.
# Thank you for the code.
# Class to stop a Thread till something happens
class Waiter():

    # Waiter Codes
    # 1 - WebSocket Server
    # 2 - App Options (Thread1)

    def __init__(self, init_value):
        self.__var = init_value
        self.__var_mutex = Lock()
        self.__var_event = Event()

    def WaitUntil(self, v):
        while True:
            self.__var_mutex.acquire()
            if self.__var == v:
                self.__var_mutex.release()
                return # Done waiting
            self.__var_mutex.release()
            self.__var_event.wait(1) # Wait 1 sec

    def Set(self, v):
        self.__var_mutex.acquire()
        self.__var = v
        self.__var_mutex.release()
        self.__var_event.set() # In case someone is waiting
        self.__var_event.clear()
    
    def Get(self):
        return self.__var


# The main app
class App():
    def __init__(self) -> None:
        # Variables
        
        self.__image = Image.open(self.resource_path("icon.png"))
        self.__waiter = Waiter(0)
        self.__state = 0
        self.__is_ws_cache_cleared = False
        self.__is_stopping = False
        self.__stop_event = Event()
        self.__audio_format_var = "mp3"
        self.__download_directory = getcwd()
        self.__download_directory_tmp = ''
        self.__output = 0



        # Threads
        self.__thread0 = Thread(name='Thread0', target=self.Thread0)
        self.__thread0.daemon = True
        self.__thread0.start()

        self.__thread1 = Thread(name='Thread1', target=self.Thread1)
        self.__thread1.daemon = True
        self.__thread1.start()

        self.__thread2 = Thread(name='Thread2', target=self.Thread2)
        self.__thread2.daemon = True
        self.__thread2.start()

        # Run server automatically
        self.__waiter.Set(1)
        self.__state = "run_download_server"

        # WebSocket
        async_run(self.ws_main())


    # I don't know from who I copied this code.
    # But if you're the creator tell me and I'll put you here.
    # Thank you for the code.
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # Download Command
    def download(self, url):
        yt_dlp = self.resource_path("yt-dlp")
        yt_dlp = '"'+yt_dlp
        yt_dlp = yt_dlp+'"'

        # Get the url but remove till an "&" to not download all the playlist
        url = url[0:url.find("&")]

        # To hide the console when executing the command
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Command that is executing in background
        self.__output = subprocess.run(f'{yt_dlp} -x --audio-format {self.__audio_format_var} -o "{self.__download_directory}/%(title)s.%(ext)s" {url}', startupinfo=si)

    # WebSocket Functions
    async def ws_main(self):
        async with websocket_serve(self.ws_loop, "localhost", 8765):
            self.__stop_condition = async_get_event_loop().run_in_executor(None, self.__stop_event.wait)
            await self.__stop_condition
    
    async def ws_loop(self, ws):

        # To clear the messages if some message was sent when the server was closed

        if self.__waiter.Get() == 1:
            self.__is_ws_cache_cleared = True
        else:
            self.__is_ws_cache_cleared = False
            self.__waiter.WaitUntil(1)
        
        try:
            async for message in ws:
                if not self.__is_ws_cache_cleared:
                    self.__is_ws_cache_cleared = True
                    return

                if message == "confirmed":
                    self.download(self.__url)
                    if (self.__output.returncode==0):
                        await ws.send("finished_0")
                    else:
                        await ws.send("finished_1")
                    self.__url = ""
                    
                    return

                self.__url = message
                await ws.send("confirmed")
                
        except:
            pass

    # Thread Functions
    def clear_threads(self):
        try:
            self.__thread0.join()
            self.__thread1.join()
            self.__thread2.join()
        except:
            pass
    
    def Thread0(self):
        def set_state(v):
            # Set the state of the app (right click on tray icon)
            def inner(icon, item):
                self.__state = v
                
                # check the state applied
                if self.__state == "run_download_server":
                    self.__waiter.Set(1)
                elif self.__state == "stop_download_server":
                    self.__waiter.Set(0)
                    self.__state = 0

                elif self.__state == "options":
                    self.__initial_waiter_value = self.__waiter.Get()
                    self.__waiter.Set(2)
                    self.__state = "run_download_server"
                    icon.visible = False
                elif self.__state == "manual_download":
                    self.__waiter.Set(3)
                    self.__state = "run_download_server"
                    icon.visible = False
                elif self.__state == "exit_app":
                    self.__stop_event.set()
                    self.__waiter.Set(1)
                    sleep(.5)
                    self.__is_stopping = True
                    self.__waiter.Set(2)
                    sleep(.5)
                    self.__waiter.Set(3)
                    icon.stop()
            return inner
        
        # Get the current state of the app
        def get_state(v):
            def inner(item):
                return self.__state == v
            return inner

        # The tray icon
        self.__icon = icon('App', icon=self.__image, menu=menu(lambda: (
            item(
                'Run Download Server',
                set_state("run_download_server"),
                checked=get_state("run_download_server"),
                radio=True
            ),
            item(
                'Stop Download Server',
                set_state("stop_download_server"),
                checked=get_state("stop_download_server"),
                radio=True
            ),
            item(
                'Manual Download',
                set_state("manual_download"),
                checked=get_state("manual_download"),
                radio=True
            ),
            item(
                'Configuration',
                set_state("options"),
                checked=get_state("options"),
                radio=True
            ),
            item(
                'Stop App',
                set_state("exit_app"),
                checked=get_state("exit_app"),
                radio=True
            ),
        )))

        try:
            self.__icon.run()
        except:
            pass
        
    def Thread1(self):
        # Change the directory where files will be saved
        def set_directory():
            while True:
                self.__download_directory_tmp = filedg.askdirectory(title="Choose Directory")
                
                if self.__download_directory_tmp == '':
                    self.__download_directory_tmp = self.__download_directory
                break
            self.__directory_show["text"] = self.__download_directory_tmp

        # Save all the changes of configuration
        def save_data():
            self.__audio_format_var = self.__audio_format.get()
            self.__download_directory = self.__download_directory_tmp

        while True:
            
            self.__waiter.WaitUntil(2)
            if self.__is_stopping:
                try:
                    self.__window.destroy()
                except:
                    pass
                break

            # Creation of all the elements
            self.__window = tk.Tk()
            self.__window.geometry("300x170")
            self.__window.resizable(True, False)
            self.__window.title("OPTIONS")

            self.__audio_format_label = tk.Label(self.__window, text="Audio Export Format: ")
            self.__audio_format_label.place(x=10, y=5)
            self.__audio_format = ttk.Combobox(
                state="readonly",
                values=["aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav", "alac"],
            )
            self.__audio_format.current(2)
            self.__audio_format.place(x=10,y=25)

            self.__directory_label = tk.Label(self.__window, text="Download Directory: ")
            self.__directory_label.place(x=10, y=55)
            self.__directory_show = tk.Label(self.__window, text=self.__download_directory)
            self.__directory_show.place(x=10, y=75)
            self.__directory_change = tk.Button(self.__window, text="Change",command=set_directory, borderwidth=1, highlightthickness=0, relief='solid', padx=5, pady=5)
            self.__directory_change.place(x=10, y=95)

            self.__apply_BT = tk.Button(self.__window, text="Apply Changes", command=save_data, borderwidth=1, highlightthickness=0, relief='solid', padx=5, pady=5)
            self.__apply_BT.place(x=10, y=130)

            self.__window.mainloop()

            self.__icon.visible = True
            self.__waiter.Set(self.__initial_waiter_value)

        # EXIT THREAD 1

        
    # The manual download thread
    def Thread2(self):
        def download():
            url = self.__download_entry_text_variable.get()
            self.__download_entry_text_variable.set("")
            if "https://www.youtube.com/watch?v=" in url:
                self.download(url)

        while True:
            self.__initial_waiter_value = self.__waiter.Get()
            self.__waiter.WaitUntil(3)
            if self.__is_stopping:
                try:
                    self.__window2.destroy()
                except:
                    pass
                break


            self.__window2 = tk.Tk()
            self.__window2.geometry("385x85")
            self.__window2.title("Manual Download")

            self.__download_label = tk.Label(self.__window2, text="Put download Link: ")
            self.__download_label.place(x=10, y=10)

            self.__download_entry_text_variable = tk.StringVar(self.__window2)
            self.__download_entry = tk.Entry(self.__window2, textvariable=self.__download_entry_text_variable, width=60)
            self.__download_entry.place(x=10, y=30)

            self.__download_button = tk.Button(self.__window2, text="Download", command=download)
            self.__download_button.place(x=10, y=50)

            self.__window2.mainloop()
            self.__icon.visible = True 
            self.__waiter.Set(self.__initial_waiter_value)
        # EXIT THREAD 2

app = App()

# We clear the threads to make sure it finishes correctly
app.clear_threads()