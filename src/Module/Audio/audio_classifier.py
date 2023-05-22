# Copyright 2023 The MediaPipe Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications:
# - Refactored the original script into the AudioClassifierRunner class

# Rest of your modified code here

import argparse
import time

from mediapipe.tasks import python
from mediapipe.tasks.python.components import containers
from mediapipe.tasks.python import audio

from src.Module.Audio.audio_record import AudioRecord


class AudioClassifierRunner:

    def __init__(self, model='lite-model_yamnet_classification.tflite',
                 max_results=3, score_threshold=0.3, overlapping_factor=0.5, queue=None, device=None):
        self.model = model
        self.max_results = max_results
        self.score_threshold = score_threshold
        self.overlapping_factor = overlapping_factor
        self.classification_result_list = []
        self.queue = queue
        self.is_recording = False
        self.device = device

    def save_result(self, result: audio.AudioClassifierResult, timestamp_ms: int):
        result.timestamp_ms = timestamp_ms
        self.classification_result_list.append(result)

    def run(self) -> None:
        if (self.overlapping_factor <= 0) or (self.overlapping_factor >= 1.0):
            raise ValueError('Overlapping factor must be between 0 and 1.')

        if (self.score_threshold < 0) or (self.score_threshold > 1.0):
            raise ValueError('Score threshold must be between (inclusive) 0 and 1.')

        base_options = python.BaseOptions(model_asset_path=self.model)
        options = audio.AudioClassifierOptions(
            base_options=base_options, running_mode=audio.RunningMode.AUDIO_STREAM,
            max_results=self.max_results, score_threshold=self.score_threshold,
            result_callback=self.save_result)
        classifier = audio.AudioClassifier.create_from_options(options)

        buffer_size, sample_rate, num_channels = 15600, 16000, 1
        audio_format = containers.AudioDataFormat(num_channels, sample_rate)
        record = AudioRecord(num_channels, sample_rate, buffer_size, device=self.device)
        audio_data = containers.AudioData(buffer_size, audio_format)

        input_length_in_second = float(len(
            audio_data.buffer)) / audio_data.audio_format.sample_rate
        interval_between_inference = input_length_in_second * (1 - self.overlapping_factor)
        pause_time = interval_between_inference * 0.1
        last_inference_time = time.time()

        record.start_recording()
        self.is_recording = True

        while True:
            while self.is_recording:
                now = time.time()
                diff = now - last_inference_time
                if diff < interval_between_inference:
                    time.sleep(pause_time)
                    continue
                last_inference_time = now

                data = record.read(buffer_size)
                audio_data.load_from_array(data)
                classifier.classify_async(audio_data, round(last_inference_time * 1000))
                if self.classification_result_list:
                    if len(self.classification_result_list[0].classifications[0].categories) > 0:
                        top_category = self.classification_result_list[0].classifications[0].categories[0]
                        # print(f"score={top_category.score}, category_name='{top_category.category_name}'")
                        if self.queue:
                            self.queue.put([top_category.score, top_category.category_name])
                            # threading.Thread(target=self.callback,
                            #                  args=(top_category.score, top_category.category_name,)).start()
                    else:
                        if self.queue:
                            self.queue.put([None, None])
                            # threading.Thread(target=self.callback, args=(None, None,)).start()

                    self.classification_result_list.clear()

    def stop(self):
        self.is_recording = False

    def start(self):
        self.is_recording = True


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--model',
        help='Name of the audio classification model.',
        required=False,
        default='lite-model_yamnet_classification.tflite')
    parser.add_argument(
        '--maxResults',
        help='Maximum number of results to show.',
        required=False,
        default=3)
    parser.add_argument(
        '--overlappingFactor',
        help='Target overlapping between adjacent inferences. Value must be in (0, 1)',
        required=False,
        default=0.5)
    parser.add_argument(
        '--scoreThreshold',
        help='The score threshold of classification results.',
        required=False,
        default=0.3)
    args = parser.parse_args()

    audio_classifier_runner = AudioClassifierRunner(args.model, int(args.maxResults),
                                                    float(args.scoreThreshold), float(args.overlappingFactor))
    audio_classifier_runner.run()


if __name__ == '__main__':
    main()
