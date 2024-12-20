import time

from src.Command.Command import Command

SILENCE_THRESHOLD = 5


class TranscribeVoiceCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.silence_start_time = None
        self.system_config = sys_config

    def execute(self):
        notification = f"I'm listening..."
        self.system_config.notification = {'notif_type': 'listening_icon',
                                           'position': 'middle-right'}
        voice_transcriber = self.system_config.get_transcriber()
        if voice_transcriber is not None:
            if voice_transcriber.stop_event.is_set():
                voice_transcriber.start()

        if voice_transcriber.mode != "voice_transcription":
            voice_transcriber.stop_emotion_classification_and_start_transcription()

        # Stop the transcriber when no voice is detected for 6 seconds
        while True:
            if self.system_config.stop_recording_command:
                self.system_config.stop_recording_command = False
                # User can manually cancel the recording if it's mistakenly triggered
                if self.system_config.cancel_recording_command:
                    self.system_config.notification = {'notif_type': 'cancel_recording_icon',
                                                       'position': 'middle-right',
                                                       'duration': 1}
                    voice_transcriber.stop_transcription_and_start_emotion_classification()
                    return ""

                self.system_config.progress_bar_percentage = None
                break
            if not self.detect_user_speak():
                if self.silence_start_time is None:
                    self.silence_start_time = time.time()
                else:
                    time_diff = time.time() - self.silence_start_time
                    self.system_config.progress_bar_percentage = (SILENCE_THRESHOLD - time_diff) / SILENCE_THRESHOLD
                    # print(f"Stop Recording in {int(SILENCE_THRESHOLD-time_diff)}s")
                    if time_diff > SILENCE_THRESHOLD:
                        self.silence_start_time = None
                        self.system_config.progress_bar_percentage = None
                        break
            else:
                self.silence_start_time = None

        self.system_config.notification = {'notif_type': 'processing_icon',
                                           'position': 'middle-right'}

        self.system_config.progress_bar_percentage = None
        time.sleep(0.5)
        full_transcription = voice_transcriber.stop_transcription_and_start_emotion_classification()
        print(f"Full transcription: {full_transcription}")

        return full_transcription

    def detect_user_speak(self):
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is None:
            return False
        # if category is speech, then return True
        if category == 'Speech':
            return True
        return False
