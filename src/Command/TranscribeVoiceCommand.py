import time

from src.Command.Command import Command

SILENCE_THRESHOLD = 5


class TranscribeVoiceCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.silence_start_time = None
        self.system_config = sys_config

    def execute(self):
        notification = f"Transcribing voice..."
        print(notification)
        self.system_config.notification = notification
        voice_transcriber = self.system_config.get_transcriber()
        if voice_transcriber is not None:
            if voice_transcriber.stop_event.is_set():
                voice_transcriber.start()

        # Stop the transcriber when no voice is detected for 6 seconds
        while True:
            if not self.detect_user_speak():
                if self.silence_start_time is None:
                    self.silence_start_time = time.time()
                else:
                    time_diff = time.time() - self.silence_start_time
                    self.system_config.notification = f"Stop Recording in {int(SILENCE_THRESHOLD-time_diff)}s"
                    print(f"Stop Recording in {int(SILENCE_THRESHOLD-time_diff)}s")
                    if time_diff > SILENCE_THRESHOLD:
                        self.silence_start_time = None
                        break
            else:
                self.silence_start_time = None
            time.sleep(0.5)

        full_transcription = voice_transcriber.stop()
        print(f"Full transcription: {full_transcription}")
        self.system_config.notification = f"Processing your command..."
        return full_transcription

    def detect_user_speak(self):
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is None:
            return False
        # if category is speech, then return True
        if category == 'Speech':
            return True
        return False