from src.Utilities.image_processor import undistort_img


class GazeData:
    def __init__(self):
        self.potential_interested_object = None
        self.original_frame = None
        self.norm_gaze_position = None
        self.zoom_in = False
        self.closest_object = None
        self.person_count = 0
        self.fixation_detected = False

    def put_potential_interested_object(self, obj):
        self.potential_interested_object = obj

    def get_potential_interested_object(self):
        return self.potential_interested_object

    def put_original_frame(self, frame):
        self.original_frame = frame

    def get_original_frame(self):
        return self.original_frame
        # if self.original_frame is None:
        #     return None
        # return undistort_img(self.original_frame)

    def put_norm_gaze_position(self, pos):
        self.norm_gaze_position = pos

    def get_norm_gaze_position(self):
        return self.norm_gaze_position

    def put_zoom_in(self, zoom):
        self.zoom_in = zoom

    def get_zoom_in(self):
        return self.zoom_in

    def put_closest_object(self, obj):
        self.closest_object = obj

    def get_closest_object(self):
        return self.closest_object

    def put_person_count(self, count):
        self.person_count = count

    def get_person_count(self):
        return self.person_count

    def put_fixation_detected(self, detected):
        self.fixation_detected = detected

    def get_fixation_detected(self):
        return self.fixation_detected
