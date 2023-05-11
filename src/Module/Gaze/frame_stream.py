import zmq
from msgpack import unpackb, packb
import numpy as np
import cv2


class PupilCamera:
    def __init__(self, frame_format="bgr"):
        self.context = zmq.Context()
        self.addr = "127.0.0.1"  # remote ip or localhost
        self.req_port = "50020"  # same as in the pupil remote gui
        self.req = self.context.socket(zmq.REQ)
        self.req.connect("tcp://{}:{}".format(self.addr, self.req_port))

        # ask for the sub port
        self.req.send_string("SUB_PORT")
        self.sub_port = self.req.recv_string()

        # open a sub port to listen to pupil
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect("tcp://{}:{}".format(self.addr, self.sub_port))

        # set subscriptions to topics
        # recv just pupil/gaze/notifications
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "frame.world")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "fixations")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "gaze.3d.01.")
        # self.sub.subscribe('fixations')  # receive all gaze messages
        # self.sub.subscribe('gaze.3d.1.')

        self.recent_world = None
        self.recent_eye0 = None
        self.recent_eye1 = None

        self.FRAME_FORMAT = frame_format

        # Set the frame format via the Network API plugin
        self.notify({"subject": "frame_publishing.set_format", "format": self.FRAME_FORMAT})

    def recv_from_sub(self):
        """Recv a message with topic, payload.
        Topic is a utf-8 encoded string. Returned as unicode object.
        Payload is a msgpack serialized dict. Returned as a python dict.
        Any addional message frames will be added as a list
        in the payload dict with key: '__raw_data__' .
        """
        topic = self.sub.recv_string()
        payload = unpackb(self.sub.recv(), raw=False)
        extra_frames = []
        while self.sub.get(zmq.RCVMORE):
            extra_frames.append(self.sub.recv())
        if extra_frames:
            payload["__raw_data__"] = extra_frames
        return topic, payload

    def has_new_data_available(self):
        # Returns True as long subscription socket has received data queued for processing
        return self.sub.get(zmq.EVENTS) & zmq.POLLIN

    def notify(self, notification):
        """Sends ``notification`` to Pupil Remote"""
        topic = "notify." + notification["subject"]
        payload = packb(notification, use_bin_type=True)
        self.req.send_string(topic, flags=zmq.SNDMORE)
        self.req.send(payload)
        return self.req.recv_string()

    def start(self):
        try:
            while True:
                # The subscription socket receives data in the background and queues it for
                # processing. Once the queue is full, it will stop receiving data until the
                # queue is being processed. In other words, the code for processing the queue
                # needs to be faster than the incoming data.
                # e.g. we are subscribed to scene (30 Hz) and eye images (2x 120 Hz), resulting
                # in 270 images per second. Displays typically only have a refresh rate of
                # 60 Hz. As a result, we cannot draw all frames even if the network was fast
                # enough to transfer them. To avoid that the processing can keep up, we only
                # display the most recently received images *after* the queue has been emptied.
                while self.has_new_data_available():
                    topic, msg = self.recv_from_sub()

                    if topic == "fixations":
                        print(
                            f"Fixation: Normal Pos: {msg['norm_pos']}, Duration: {msg['duration']}, Confidence: {msg['confidence']}")

                    if topic.startswith("frame.") and msg["format"] != self.FRAME_FORMAT:
                        print(
                            f"different frame format ({msg['format']}); "
                            f"skipping frame from {topic}"
                        )
                        continue

                    if topic == "frame.world":
                        self.recent_world = np.frombuffer(
                            msg["__raw_data__"][0], dtype=np.uint8
                        ).reshape(msg["height"], msg["width"], 3)
                    elif topic == "frame.eye.0":
                        self.recent_eye0 = np.frombuffer(
                            msg["__raw_data__"][0], dtype=np.uint8
                        ).reshape(msg["height"], msg["width"], 3)
                    elif topic == "frame.eye.1":
                        self.recent_eye1 = np.frombuffer(
                            msg["__raw_data__"][0], dtype=np.uint8
                        ).reshape(msg["height"], msg["width"], 3)

                if (
                        self.recent_world is not None
                        and self.recent_eye0 is not None
                        and self.recent_eye1 is not None
                ):
                    cv2.imshow("world", self.recent_world)
                    cv2.imshow("eye0", self.recent_eye0)
                    cv2.imshow("eye1", self.recent_eye1)
                    cv2.waitKey(1)
                    pass  # here you can do calculation on the 3 most recent world, eye0 and eye1 images
        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()


if __name__ == '__main__':
    camera = PupilCamera(frame_format="bgr")
    camera.start()
