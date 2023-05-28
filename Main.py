import os, pyttsx3, requests, dotenv, soundfile, sounddevice, openai, unicodedata, time, json, pytchat, colorama, datetime

dotenv.load_dotenv(dotenv.find_dotenv())
openai.api_key = os.getenv("OAI_API_KEY")

def checker(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            return result
        
        except Exception as error:
            print(colorama.Fore.RED + "> Error trying to execute function: {0} | {1} seconds".format(func.__name__, (time.time() - start_time)) + colorama.Fore.WHITE)

            if bool(os.getenv("DEBUG")):
                raise error

    return wrapper

class AI:
    def __init__(self, lore: str = "", context: list = [], video_id: str = "", source: str = "") -> None:
        self.Engine = None
        self.Context = context
        self.Lore = lore
        self.Video = video_id
        self.Source = source

        self.OAI_API_KEY = os.getenv("OAI_API_KEY")
        self.EL_API_KEY = os.getenv("EL_API_KEY")
    
    @checker
    def check_error() -> None:
        raise Exception("Test")
    
    @checker
    def set_lore(self, path: str = "data/Lore.txt") -> None:
        if len(self.Lore) < 1:
            with open(path, "r") as file:
                content = file.read()
                file.close()
        
            self.Lore = content
            
        self.Context.append({"role": "system", "content": self.Lore})
        
    @checker
    def create_engine(self) -> None:
        self.Engine = pyttsx3.init()
        self.Engine.setProperty("volume", 1)
        self.Engine.setProperty("rate", 180)

        voice = self.Engine.getProperty("voice")
        self.Engine.setProperty("voice", voice[1])
        
    @checker
    def create_response(self, message: str) -> str:
        if len(" ".join(x["content"] for x in self.Context)) >= 3900:
            self.Context = []
            self.Context.append({"role": "system", "content": self.Lore})

        message = message.replace("\n", " ")
        message = unicodedata.normalize("NFKD", message).encode("ascii", "ignore").decode("utf-8")

        self.Context.append({"role": "user", "content": message})

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.Context
        )

        self.Context.append({"role": "assistant", "content": completion.choices[0].message.content})

        with open("data/Messages.json", "r") as file:
            data = json.load(file)
            new_data = {}

            new_data["input"] = message
            new_data["output"] = completion.choices[0].message.content
            new_data["source"] = self.Source
            new_data["date"] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            data["message_{0}".format(len(data) + 1)] = new_data

            file.close()

        with open("data/Messages.json", "w", encoding="utf-8") as file:
            json.dump(data, file)
            file.close()

        return completion.choices[0].message.content
    
    @checker
    def create_tts(self, message: str) -> None:
        url = "https://api.elevenlabs.io/v1/text-to-speech/{0}".format(os.getenv("VOICE"))

        headers = {
            "accept": "audio/mpeg",
            "xi-api-key": self.EL_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "text": message,
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75
            },
            "labels": {
                "accent": "British",
                "gender": "Female"
            }
        }

        response = requests.post(url=url, headers=headers, json=data, stream=True)
        
        with open("temp/audio.mp4", "wb") as file:
            file.write(response.content)

        audio, sample_rate = soundfile.read("temp/audio.mp4")
        sounddevice.play(audio * (10 ** (7 / 20)), samplerate=sample_rate)
        sounddevice.wait()
    
    @checker
    def get_message_from_youtube(self, capacity: int) -> None:
        connection = pytchat.create(video_id=self.Video)
        chat = pytchat.create(video_id=self.Video, processor=pytchat.SpeedCalculator(capacity=capacity))

        while connection.is_alive():
            for msg in connection.get().sync_items():
                print(colorama.Fore.BLUE + "> Reading chat content..." + colorama.Fore.WHITE)

                msg, author = msg.message, msg.author.name[0:5]
                print("> {0}: {1}".format(author, msg))
                
                response = self.create_response(message="Message from {0}: {1}".format(msg, author))
                print("> Response: {0}\n".format(response))
                self.create_tts(response)

                if chat.get() >= capacity:
                    connection.terminate()
                    chat.terminate()
                    return
                
                time.sleep(1)
    
    @checker
    def init(self, lore_path: str = "data/Lore.txt"):
        self.set_lore(path=lore_path)
        self.create_engine()

def main():
    os.system("title Virtual Waifu")
    os.system("cls")

    print("1 - Use in console\n2 - Youtube streaming")
    option = int(input("> Option: "))

    assert option < 3 and option > 0, colorama.Fore.RED + "> Invalid option" + colorama.Fore.WHITE
    os.system("cls")

    if option == 1:
        username = str(input("> Username: "))

        ai = AI(source="Console")
        ai.init()

        while True:
            print(colorama.Fore.BLUE + "\n> Reading message..." + colorama.Fore.WHITE)
            message = str((input("> Message: ")))

            response = ai.create_response(message="Message from {0}: {1}".format(username, message))
            print("> Response: {0}".format(response))

            ai.create_tts(message=response)

    elif option == 2:
        video_id = str(input("> Video ID: "))
        
        ai = AI(video_id=video_id, source="Youtube")
        ai.init()
        
        while True:
            time.sleep(1.5)
            ai.get_message_from_youtube(capacity=20)

if __name__ == "__main__":
    main()