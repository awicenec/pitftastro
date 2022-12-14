# -*- coding: utf-8 -*-
#  piTFT touchscreen handling using evdev

import os

try:
    import evdev
except ImportError:
    print(
        "Evdev package is not installed.  Run 'pip3 install evdev' or 'pip install evdev' (Python 2.7) to install."
    )
    raise (ImportError("Evdev package not found."))
import logging
import queue
import threading

from settings import ROTATION, TOUCH_DEVICE

logger = logging.getLogger("pitftastro.libs.pitfttouchscreen")


# Class for handling events from piTFT
class PiTFTTouchscreen(threading.Thread):
    def __init__(
        self, device_path=TOUCH_DEVICE or "/dev/input/event2", grab=False
    ):
        super(PiTFTTouchscreen, self).__init__()
        self.device_path = device_path
        self.grab = grab
        self.events = queue.Queue()
        self.shutdown = threading.Event()

    def run(self):
        thread_process = threading.Thread(target=self.process_device)
        # run thread as a daemon so it gets cleaned up on exit.
        thread_process.daemon = True
        thread_process.start()
        self.shutdown.wait()

    # thread function
    def process_device(self):
        device = None
        # if the path to device is not found, InputDevice raises an OSError
        # exception.  This will handle it and close thread.
        try:
            device = evdev.InputDevice(self.device_path)
            if self.grab:
                device.grab()
        except Exception as ex:
            message = (
                "Unable to load device {0} due to a {1} exception with"
                " message: {2}.".format(
                    self.device_path, type(ex).__name__, str(ex)
                )
            )
            raise Exception(message)
        finally:
            if device is None:
                self.shutdown.set()
        # Loop for getting evdev events
        event = {"time": None, "id": None, "x": None, "y": None, "touch": None}
        dropping = False
        while not self.shutdown.is_set():
            for input_event in device.read_loop():
                if input_event.type == evdev.ecodes.EV_ABS:
                    if input_event.code == evdev.ecodes.ABS_X:
                        event["x"] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_Y:
                        event["y"] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                        event["id"] = input_event.value
                        if input_event.value == -1:
                            event["x"] = None
                            event["y"] = None
                            event["touch"] = None
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_X:
                        pass
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                        pass
                elif input_event.type == evdev.ecodes.EV_KEY:
                    event["touch"] = input_event.value
                elif input_event.type == evdev.ecodes.SYN_REPORT:
                    if dropping:
                        event["x"] = None
                        event["y"] = None
                        event["touch"] = None
                        dropping = False
                    else:
                        event["time"] = input_event.timestamp()
                        self.events.put(event)
                        e = event
                        event = {"x": e["x"], "y": e["y"]}
                        try:
                            event["id"] = e["id"]
                        except KeyError:
                            event["id"] = None
                        try:
                            event["touch"] = e["touch"]
                        except KeyError:
                            event["touch"] = None
                elif input_event.type == evdev.ecodes.SYN_DROPPED:
                    dropping = True
        if self.grab:
            device.ungrab()

    def get_event(self):
        if not self.events.empty():
            event = self.events.get()
            yield event
        else:
            yield None

    def queue_empty(self):
        return self.events.empty()

    def stop(self):
        self.shutdown.set()

    def __del__(self):
        self.shutdown.set()


# Here we convert the evdev "hardware" touch coordinates into pygame surface pixel coordinates
def get_pixels_from_coordinates(framebuffer, coords):
    surface_size = (framebuffer.size[1], framebuffer.size[0])
    if ROTATION == 90:
        tft_orig = (3750, 180)
        tft_end = (150, 3750)
    elif ROTATION == 270:
        tft_orig = (150, 3750)
        tft_end = (3750, 180)
    else:
        logger.error("Invalid rotation")
        tft_orig = (150, 3750)
        tft_end = (3750, 180)

    tft_delta = (tft_end[0] - tft_orig[0], tft_end[1] - tft_orig[1])
    tft_abs_delta = (
        abs(tft_end[0] - tft_orig[0]),
        abs(tft_end[1] - tft_orig[1]),
    )

    if tft_delta[0] < 0:
        y = (
            float(tft_abs_delta[0] - coords[0] + tft_end[0])
            / float(tft_abs_delta[0])
            * float(surface_size[0])
        )
    else:
        y = (
            float(coords[0] - tft_orig[0])
            / float(tft_abs_delta[0])
            * float(surface_size[0])
        )
    if tft_delta[1] < 0:
        x = (
            float(tft_abs_delta[1] - coords[1] + tft_end[1])
            / float(tft_abs_delta[1])
            * float(surface_size[1])
        )
    else:
        x = (
            float(coords[1] - tft_orig[1])
            / float(tft_abs_delta[1])
            * float(surface_size[1])
        )
    return int(x), int(y)
