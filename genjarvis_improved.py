import tkinter as tk
from tkinter import scrolledtext, PhotoImage, ttk
import threading
import pyttsx3
import datetime
import os
import webbrowser
import time
import sys
import wikipedia
import subprocess

# Optional imports that can be commented out if not available
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class GenJarvisUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GenJARVIS Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e2e")
        
        # Initialize speech engine
        self.engine = pyttsx3.init()
        self.listening = False
        
        # Initialize model (if available)
        self.llm = None
        if LLAMA_AVAILABLE:
            try:
                self.llm = Llama(model_path="models/llama-2-7b-chat.Q4_K_M.gguf", n_ctx=512)
            except Exception as e:
                print(f"LLaMA model initialization error: {e}")
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Top frame with title
        top_frame = tk.Frame(self.root, bg="#1e1e2e")
        top_frame.pack(pady=10)
        
        title_label = tk.Label(
            top_frame, 
            text="GenJARVIS", 
            font=("Helvetica", 20, "bold"),
            fg="#cba6f7",
            bg="#1e1e2e"
        )
        title_label.pack()
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg="#282a36",
            fg="#f8f8f2",
            font=("Consolas", 11),
            height=15
        )
        self.chat_display.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input and buttons frame
        input_frame = tk.Frame(self.root, bg="#1e1e2e")
        input_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Text input
        self.text_input = tk.Entry(
            input_frame,
            font=("Consolas", 11),
            bg="#282a36",
            fg="#f8f8f2",
            insertbackground="#f8f8f2"
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
        self.text_input.bind("<Return>", self.on_enter_pressed)
        
        # Send button
        send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.process_text_input,
            bg="#cba6f7",
            fg="#282a36",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=10
        )
        send_button.pack(side=tk.RIGHT, padx=5)
        
        # Voice button
        self.voice_button = tk.Button(
            input_frame,
            text="🎤 Voice",
            command=self.toggle_voice_input,
            bg="#94e2d5" if SR_AVAILABLE else "#6c7086",
            fg="#282a36",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=10
        )
        self.voice_button.pack(side=tk.RIGHT, padx=5)
        
        # Quick commands frame
        commands_frame = tk.Frame(self.root, bg="#1e1e2e")
        commands_frame.pack(pady=10, fill=tk.X)
        
        # Quick command buttons
        commands = [
            ("🕒 Time", self.get_time),
            ("🌐 Chrome", lambda: self.open_app("chrome")),
            ("🎵 Music", self.play_music),
            ("🔍 Search", self.web_search),
            ("📰 News", lambda: self.web_search("latest news")),
            ("❓ Help", self.show_help)
        ]
        
        for text, command in commands:
            button = tk.Button(
                commands_frame,
                text=text,
                command=command,
                bg="#313244",
                fg="#cdd6f4",
                font=("Helvetica", 9),
                relief=tk.FLAT,
                padx=5
            )
            button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            bg="#11111b",
            fg="#cdd6f4"
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Welcome message
        self.update_chat("GenJARVIS", "Welcome! How can I assist you today?")
        self.speak("Welcome! How can I assist you today?")
    
    def update_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        if sender == "User":
            self.chat_display.insert(tk.END, f"\n[{timestamp}] You: ", "user_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "user_msg")
        else:
            self.chat_display.insert(tk.END, f"\n[{timestamp}] GenJARVIS: ", "jarvis_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "jarvis_msg")
        
        self.chat_display.tag_config("user_tag", foreground="#f38ba8", font=("Consolas", 11, "bold"))
        self.chat_display.tag_config("user_msg", foreground="#f8f8f2", font=("Consolas", 11))
        self.chat_display.tag_config("jarvis_tag", foreground="#89dceb", font=("Consolas", 11, "bold"))
        self.chat_display.tag_config("jarvis_msg", foreground="#f8f8f2", font=("Consolas", 11))
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def speak(self, text):
        # Run in a separate thread to prevent UI freezing
        def speak_thread():
            self.engine.say(text)
            self.engine.runAndWait()
            
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def listen(self):
        if not SR_AVAILABLE:
            self.update_chat("GenJARVIS", "Speech recognition is not available. Please install the required packages.")
            self.speak("Speech recognition is not available. Please install the required packages.")
            return ""
        
        recognizer = sr.Recognizer()
        self.status_var.set("Listening...")
        
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                self.root.update()
                audio = recognizer.listen(source, timeout=5)
                self.status_var.set("Processing speech...")
                self.root.update()
                
                # Try using Google's speech recognition
                try:
                    text = recognizer.recognize_google(audio)
                    return text.lower()
                except:
                    self.status_var.set("Couldn't understand audio")
                    return ""
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            return ""
        finally:
            self.status_var.set("Ready")
            self.listening = False
            self.voice_button.config(bg="#94e2d5")
    
    def toggle_voice_input(self):
        if not SR_AVAILABLE:
            self.update_chat("GenJARVIS", "Speech recognition not available. Please install 'speech_recognition' package.")
            return
            
        if self.listening:
            self.listening = False
            self.voice_button.config(bg="#94e2d5")
            self.status_var.set("Voice input cancelled")
        else:
            self.voice_button.config(bg="#f38ba8")
            self.listening = True
            
            # Start listening in a thread to keep UI responsive
            def listen_thread():
                text = self.listen()
                if text:
                    self.update_chat("User", text)
                    self.handle_command(text)
            
            threading.Thread(target=listen_thread, daemon=True).start()
    
    def process_text_input(self):
        user_input = self.text_input.get().strip()
        if user_input:
            self.update_chat("User", user_input)
            self.text_input.delete(0, tk.END)
            self.handle_command(user_input)
    
    def on_enter_pressed(self, event):
        self.process_text_input()
    
    def llama_response(self, prompt):
        if not LLAMA_AVAILABLE or self.llm is None:
            return "I'm running in basic mode without LLM capabilities. Please install llama-cpp-python and download a model to enable smart responses."
        
        try:
            self.status_var.set("Thinking...")
            self.root.update()
            # Format the prompt for chat-like behavior
            formatted_prompt = f"User: {prompt}\nJARVIS:"
            output = self.llm(formatted_prompt, max_tokens=150, stop=["User:", "JARVIS:"], echo=False)
            response = output["choices"][0]["text"].strip()
            return response
        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}"
        finally:
            self.status_var.set("Ready")
    
    def handle_command(self, command):
        command = command.lower()
        
        # Basic commands
        if 'open chrome' in command:
            self.open_app("chrome")
        elif 'open code' in command or 'open vs code' in command:
            self.open_app("code")
        elif 'play music' in command or 'play song' in command:
            self.play_music()
        elif 'time' in command:
            self.get_time()
        elif 'search' in command:
            search_term = command.replace("search", "").strip()
            self.web_search(search_term)
        elif 'who is' in command or 'what is' in command:
            self.wiki_search(command)
        elif 'exit' in command or 'quit' in command or 'close' in command:
            self.exit_application()
        elif 'joke' in command:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "Parallel lines have so much in common. It's a shame they'll never meet.",
                "Why did the scarecrow win an award? Because he was outstanding in his field!"
            ]
            import random
            joke = random.choice(jokes)
            self.update_chat("GenJARVIS", joke)
            self.speak(joke)
        elif 'weather' in command:
            self.web_search("weather")
        elif 'news' in command:
            self.web_search("latest news")
        elif 'help' in command:
            self.show_help()
        else:
            # Use LLaMA for conversation if available
            response = self.llama_response(command)
            self.update_chat("GenJARVIS", response)
            self.speak(response)
    
    def open_app(self, app_name):
        try:
            if app_name == "chrome":
                response = "Opening Chrome."
                if sys.platform == "win32":
                    os.system("start chrome")
                elif sys.platform == "darwin":
                    os.system("open -a 'Google Chrome'")
                else:
                    os.system("google-chrome")
            elif app_name == "code":
                response = "Opening Visual Studio Code."
                if sys.platform == "win32":
                    os.system("code")
                else:
                    os.system("code")
            
            self.update_chat("GenJARVIS", response)
            self.speak(response)
        except Exception as e:
            self.update_chat("GenJARVIS", f"Failed to open {app_name}: {str(e)}")
    
    def play_music(self):
        self.update_chat("GenJARVIS", "What song would you like to listen to?")
        self.speak("What song would you like to listen to?")
        
        def on_song_submit():
            song_name = song_entry.get().strip()
            if song_name:
                dialog.destroy()
                self.update_chat("User", f"Play {song_name}")
                self.update_chat("GenJARVIS", f"Playing {song_name} on YouTube.")
                self.speak(f"Playing {song_name} on YouTube")
                
                # Open YouTube with the search query
                search_query = song_name.replace(" ", "+")
                webbrowser.open(f"https://www.youtube.com/results?search_query={search_query}")
        
        # Create a dialog for song input
        dialog = tk.Toplevel(self.root)
        dialog.title("Play Music")
        dialog.geometry("400x150")
        dialog.configure(bg="#1e1e2e")
        
        tk.Label(
            dialog, 
            text="Enter a song name:", 
            fg="#cdd6f4", 
            bg="#1e1e2e",
            font=("Helvetica", 12)
        ).pack(pady=10)
        
        song_entry = tk.Entry(
            dialog, 
            font=("Consolas", 11),
            bg="#282a36",
            fg="#f8f8f2",
            width=30
        )
        song_entry.pack(pady=10)
        song_entry.focus_set()
        
        submit_btn = tk.Button(
            dialog, 
            text="Play", 
            command=on_song_submit,
            bg="#cba6f7",
            fg="#282a36",
            font=("Helvetica", 10, "bold")
        )
        submit_btn.pack(pady=10)
        
        # Bind Enter key
        song_entry.bind("<Return>", lambda event: on_song_submit())
    
    def get_time(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        response = f"The current time is {now}"
        self.update_chat("GenJARVIS", response)
        self.speak(response)
    
    def web_search(self, query=None):
        if not query:
            self.update_chat("GenJARVIS", "What would you like to search for?")
            self.speak("What would you like to search for?")
            
            def on_search_submit():
                search_term = search_entry.get().strip()
                if search_term:
                    dialog.destroy()
                    self.update_chat("User", f"Search for {search_term}")
                    self.update_chat("GenJARVIS", f"Searching for {search_term}")
                    self.speak(f"Searching for {search_term}")
                    search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                    webbrowser.open(search_url)
            
            # Create dialog for search input
            dialog = tk.Toplevel(self.root)
            dialog.title("Web Search")
            dialog.geometry("400x150")
            dialog.configure(bg="#1e1e2e")
            
            tk.Label(
                dialog, 
                text="Enter your search term:", 
                fg="#cdd6f4", 
                bg="#1e1e2e",
                font=("Helvetica", 12)
            ).pack(pady=10)
            
            search_entry = tk.Entry(
                dialog, 
                font=("Consolas", 11),
                bg="#282a36",
                fg="#f8f8f2",
                width=30
            )
            search_entry.pack(pady=10)
            search_entry.focus_set()
            
            submit_btn = tk.Button(
                dialog, 
                text="Search", 
                command=on_search_submit,
                bg="#cba6f7",
                fg="#282a36",
                font=("Helvetica", 10, "bold")
            )
            submit_btn.pack(pady=10)
            
            # Bind Enter key
            search_entry.bind("<Return>", lambda event: on_search_submit())
        else:
            self.update_chat("GenJARVIS", f"Searching for {query}")
            self.speak(f"Searching for {query}")
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
    
    def wiki_search(self, query):
        # Remove question phrases
        for phrase in ["who is", "what is", "tell me about"]:
            query = query.replace(phrase, "").strip()
        
        try:
            self.status_var.set(f"Searching Wikipedia for {query}...")
            self.root.update()
            result = wikipedia.summary(query, sentences=2)
            self.update_chat("GenJARVIS", result)
            self.speak(result)
        except Exception as e:
            response = f"I couldn't find information about {query}. Would you like me to search the web instead?"
            self.update_chat("GenJARVIS", response)
            self.speak(response)
        finally:
            self.status_var.set("Ready")
    
    def show_help(self):
        help_text = """
Available commands:
- "Time" - Get the current time
- "Open Chrome" - Launch Chrome browser
- "Open VS Code" - Launch Visual Studio Code
- "Play music" - Search and play music on YouTube
- "Search [query]" - Search the web
- "Who is [person]" - Get Wikipedia information
- "What is [thing]" - Get Wikipedia information
- "Weather" - Check the weather
- "News" - Get the latest news
- "Joke" - Tell a joke
- "Exit/Quit" - Close the application

You can type commands or use the voice button to speak.
        """
        self.update_chat("GenJARVIS", help_text)
        self.speak("Here are some commands you can use with me.")
    
    def exit_application(self):
        self.update_chat("GenJARVIS", "Goodbye! Have a great day!")
        self.speak("Goodbye! Have a great day!")
        self.root.after(2000, self.root.destroy)

def main():
    root = tk.Tk()
    app = GenJarvisUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
