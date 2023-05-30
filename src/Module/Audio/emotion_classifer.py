import whisper
from torch import device as torch_device, cuda, nn
from torch.nn.functional import softmax
from torchaudio.transforms import Resample
import torchaudio
from transformers import AutoConfig, Wav2Vec2FeatureExtractor, pipeline

from torch.nn import BCEWithLogitsLoss, CrossEntropyLoss, MSELoss
import os.path
import threading
import time
import wavio as wv

import numpy as np
import sounddevice as sd
from src.Module.Audio.audio_record import AudioRecord

from transformers.models.wav2vec2.modeling_wav2vec2 import (
    Wav2Vec2PreTrainedModel,
    Wav2Vec2Model
)

import ssl

from src.Module.Audio.live_transcriber import show_devices
from typing import Optional, Tuple
import torch
from transformers.file_utils import ModelOutput

ssl._create_default_https_context = ssl._create_unverified_context


class SpeechClassifierOutput(ModelOutput):
    loss: Optional[torch.FloatTensor] = None
    logits: torch.FloatTensor = None
    hidden_states: Optional[Tuple[torch.FloatTensor]] = None
    attentions: Optional[Tuple[torch.FloatTensor]] = None


class Wav2Vec2ClassificationHead(nn.Module):
    """Head for wav2vec classification task."""

    def __init__(self, config):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, features, **kwargs):
        x = features
        x = self.dropout(x)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class Wav2Vec2ForSpeechClassification(Wav2Vec2PreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.pooling_mode = config.pooling_mode
        self.config = config

        self.wav2vec2 = Wav2Vec2Model(config)
        self.classifier = Wav2Vec2ClassificationHead(config)

        self.init_weights()

    def freeze_feature_extractor(self):
        self.wav2vec2.feature_extractor._freeze_parameters()

    def merged_strategy(
            self,
            hidden_states,
            mode="mean"
    ):
        if mode == "mean":
            outputs = torch.mean(hidden_states, dim=1)
        elif mode == "sum":
            outputs = torch.sum(hidden_states, dim=1)
        elif mode == "max":
            outputs = torch.max(hidden_states, dim=1)[0]
        else:
            raise Exception(
                "The pooling method hasn't been defined! Your pooling mode must be one of these ['mean', 'sum', 'max']")

        return outputs

    def forward(
            self,
            input_values,
            attention_mask=None,
            output_attentions=None,
            output_hidden_states=None,
            return_dict=None,
            labels=None,
    ):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        outputs = self.wav2vec2(
            input_values,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        hidden_states = outputs[0]
        hidden_states = self.merged_strategy(hidden_states, mode=self.pooling_mode)
        logits = self.classifier(hidden_states)

        loss = None
        if labels is not None:
            if self.config.problem_type is None:
                if self.num_labels == 1:
                    self.config.problem_type = "regression"
                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
                    self.config.problem_type = "single_label_classification"
                else:
                    self.config.problem_type = "multi_label_classification"

            if self.config.problem_type == "regression":
                loss_fct = MSELoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels)
            elif self.config.problem_type == "single_label_classification":
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            elif self.config.problem_type == "multi_label_classification":
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(logits, labels)

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return SpeechClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )


class EmotionClassifier:
    def __init__(self, model_name_or_path="harshit345/xlsr-wav2vec-speech-emotion-recognition", device_index=1,
                 duration=60, silence_threshold=0.02, overlapping_factor=0):
        self.device = torch_device("cuda" if cuda.is_available() else "cpu")
        self.config = AutoConfig.from_pretrained(model_name_or_path)
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name_or_path)
        self.model = Wav2Vec2ForSpeechClassification.from_pretrained(model_name_or_path).to(self.device)
        self.sampling_rate = self.feature_extractor.sampling_rate

        self.device_index = device_index
        self.duration = duration
        self.silence_threshold = silence_threshold
        self.overlapping_factor = overlapping_factor
        self.stop_event = threading.Event()
        self.transcribe_lock = threading.Lock()
        self.model = whisper.load_model("small.en")

        device = sd.query_devices(device_index)
        channels = device['max_input_channels']
        sample_rate = int(device['default_samplerate'])
        self.audio_record = AudioRecord(channels, sample_rate, int(duration * sample_rate), device_index)
        self.scores = None

    def speech_file_to_array_fn(self, path):
        speech_array, _sampling_rate = torchaudio.load(path)
        resampler = Resample(_sampling_rate)
        speech = resampler(speech_array).squeeze().numpy()
        return speech

    def transcribe(self, file_path):
        audio = whisper.load_audio(file_path)
        original_audio = audio
        options = whisper.DecodingOptions(language='en', fp16=False)

        # require the lock here
        with self.transcribe_lock:
            result = self.model.transcribe(
                original_audio,
                no_speech_threshold=0.2,
                logprob_threshold=None,
                verbose=False,
                **options.__dict__
            )
            # self.prompt = result['text']

            # print(result['text'])
            classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base",
                                  return_all_scores=True)
            # Flattening the data
            data = classifier(result['text'])[0]

            # Create a dictionary to store scores
            score_dict = {}

            # Iterating over the data and storing scores in dictionary
            for d in data:
                score_dict[d['label']] = d['score']

            # print(f"Joy score: {score_dict['joy']}", f"Surprise score: {score_dict['surprise']}")
            self.scores = score_dict

    def emotion_analyze(self, file_path):
        speech = self.speech_file_to_array_fn(file_path)
        inputs = self.feature_extractor(speech, sampling_rate=self.sampling_rate, return_tensors="pt", padding=True)
        inputs = {key: inputs[key].to(self.device) for key in inputs}
        with torch.no_grad():
            logits = self.model(**inputs).logits
        scores = softmax(logits, dim=1).detach().cpu().numpy()[0]
        outputs = [{"Emotion": self.config.id2label[i], "Score": f"{round(score * 100, 3):.1f}%"} for i, score in
                   enumerate(scores)]
        print(outputs)
        return outputs

    def run(self):
        self.audio_record.start_recording()
        self.is_recording = True

        dir_path = os.path.join("data", "audio")
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        idx = 0
        recording_started = False
        recording_start_time = 0

        self.silence_duration = 0
        silence_start_time = 0
        silence_start = False

        recording_thread_start_time_now = time.time()

        while not self.stop_event.is_set():
            now = time.time()

            if now - recording_thread_start_time_now < 1:
                time.sleep(1)
                continue

            previous_1s_audio = self.audio_record.read(self.audio_record.sampling_rate * 1)

            rms = np.sqrt(np.mean(np.square(previous_1s_audio)))

            diff_since_start = now - recording_start_time

            if rms <= self.silence_threshold:
                if not silence_start:
                    silence_start = True
                    silence_start_time = now
                self.silence_duration = now - silence_start_time
            else:
                silence_start = False

            if (rms <= self.silence_threshold or diff_since_start >= self.duration - 1) and recording_started:
                recording_started = False

                buffer_size = int((diff_since_start + 1) * self.audio_record.sampling_rate)
                data = self.audio_record.read(buffer_size)

                idx += 1
                idx %= 3
                file_path = os.path.join(dir_path, f"emotion{idx}.wav")
                wv.write(file_path, data, self.audio_record.sampling_rate, sampwidth=2)

                threading.Thread(target=self.transcribe, args=(file_path,)).start()

            elif rms > self.silence_threshold and not recording_started:
                recording_started = True
                recording_start_time = now

    def start(self):
        self.stop_event.clear()
        self.record_thread = threading.Thread(target=self.run)
        self.record_thread.start()

    def stop(self):
        self.stop_event.set()
        self.record_thread.join()


if __name__ == '__main__':
    show_devices()
    device_index = input("Enter device index: ")

    transcriber = EmotionClassifier(device_index=device_index)
    transcriber.start()
    input("Press Enter to stop recording...")
    print(transcriber.stop())
