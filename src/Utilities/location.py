import sys
import threading
import subprocess

import geocoder
from geopy.geocoders import Nominatim

if sys.platform == "darwin":
    from Foundation import NSObject, NSRunLoop, NSDate
    from CoreLocation import CLLocationManager


class LocationDelegate(NSObject):
    location = None
    location_updated_event = None

    def init(self):
        self.location = None
        self.location_updated_event = threading.Event()
        return self

    def locationManager_didUpdateToLocation_fromLocation_(self, manager, newLocation, oldLocation):
        if newLocation is None:
            return
        if oldLocation is None:
            pass
        elif (
            newLocation.coordinate().longitude == oldLocation.coordinate().longitude
            and newLocation.coordinate().latitude == oldLocation.coordinate().latitude
            and newLocation.horizontalAccuracy() == oldLocation.horizontalAccuracy()
        ):
            return

        geolocator = Nominatim(user_agent="UbiLoc")
        self.location = geolocator.reverse(f"{newLocation.coordinate().latitude}, {newLocation.coordinate().longitude}")
        manager.stopUpdatingLocation()
        self.location_updated_event.set()

    def get_location(self):
        if self.location is not None:
            return self.location.address
        else:
            return None

    def locationManager_didFailWithError_(self, manager, error):
        manager.stopUpdatingLocation()
        self.location_updated_event.set()
        raise Exception(f"Error: {error.localizedDescription()}")


def get_current_location_macos():
    try:
        manager = CLLocationManager.alloc().init()
        delegate = LocationDelegate.alloc().init()
        manager.setDelegate_(delegate)
        manager.startUpdatingLocation()

        run_loop = NSRunLoop.currentRunLoop()

        while not delegate.location_updated_event.is_set():
            run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))

        return delegate.get_location()
    except Exception as e:
        try:
            command = "echo \"{LAT}N {LON}E\" | shortcuts run \"Get Location\""
            result = subprocess.run(command, shell=True, text=True, capture_output=True)

            if result.returncode == 0:
                lat_lon = result.stdout.strip()
                geolocator = Nominatim(user_agent="UbiLoc")
                location = geolocator.reverse(lat_lon)
                return location.address if location else "Unknown location"
            else:
                print("Please add the 'Get Location' shortcut to your Shortcuts app: https://www.icloud.com/shortcuts/a8ce742fb5fe43caacb91bdca72a877f.")
                return None
        except Exception as shortcut_error:
            print(f"An error occurred: {shortcut_error}. Please add the 'Get Location' shortcut to your Shortcuts app: https://www.icloud.com/shortcuts/a8ce742fb5fe43caacb91bdca72a877f.")
            return None


def get_current_location_based_on_ip():
    g = geocoder.ip('me')
    if g.ok:
        geolocator = Nominatim(user_agent="UbiLoc")
        location = geolocator.reverse(f"{g.lat}, {g.lng}")
        return location.address if location else "Unknown location"
    else:
        return "Unable to determine location via IP."


def get_current_location():
    # run the below code if the system is macOS
    if sys.platform == "darwin":
        try:
            return get_current_location_macos()
        except Exception as e:
            print(f"Error during macOS location retrieval: {e}")
            return "Location retrieval failed."
    else:
        # use the IP address to get the location
        return get_current_location_based_on_ip()


if __name__ == "__main__":
    current_location = get_current_location()
    print(f"Current location: {current_location}")
