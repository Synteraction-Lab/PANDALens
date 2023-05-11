import sys
import threading

import geocoder
from Foundation import NSObject, NSRunLoop, NSDate
from CoreLocation import CLLocationManager
from geopy.geocoders import Nominatim


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
        print(f"Error: {error.localizedDescription()}")
        manager.stopUpdatingLocation()
        self.location_updated_event.set()
        sys.exit()


def get_current_location_macos():
    manager = CLLocationManager.alloc().init()
    delegate = LocationDelegate.alloc().init()
    manager.setDelegate_(delegate)
    manager.startUpdatingLocation()

    run_loop = NSRunLoop.currentRunLoop()

    while not delegate.location_updated_event.is_set():
        run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))

    return delegate.get_location()


def get_current_location_based_on_ip():
    g = geocoder.ip('me')
    if g.ok:
        geolocator = Nominatim(user_agent="UbiLoc")
        location = geolocator.reverse(f"{g.lat}, {g.lng}")
        return location
    else:
        return None


def get_current_location():
    # run the below code if the system is macOS
    if sys.platform == "darwin":
        return get_current_location_macos()
    else:
        # use the IP address to get the location
        return get_current_location_based_on_ip()


if __name__ == "__main__":
    current_location = get_current_location()
    print(f"Current location: {current_location}")
