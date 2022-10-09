# PiTFTAstro

This is a display manager for framebuffer devices which will include some apps to display status information from INDI devices on a 3.5" display on a Raspberry Pi.

## What's a display manager?

Simply put, a display manager is an application that provides other applications with access to the display.
In practice, this means you can create your own apps for it, switch between apps on the fly, and more!

## Why PiTFT?

The Adafruit PiTFT 3.5" is the target device, so I chose to reference it in the name.

## What apps come with it?

* `system` - displays system information
* `weather` - displays the current weather

## Creating apps

Creating apps is simple, each app is a Python module that provides an `App` class,
which should inherit from the `apps.AbstractApp` class. Then you just need to implement
the `run_iteration` method and have it do whatever you want the app to do!

More documentation for development coming soon.

## Installation

NOTE: This will be changed to use both PyPi and the Makefile. For the 'operational' installation on the Raspberry the systemd service should be put in place.

* First, clone the repository onto the Raspberry Pi, I recommend cloning it to `~/pitftastro` and then change directory into it.
* Second, install the required Python libraries.
* Third, copy the `pitftastro.service` file into `/etc/systemd/system`.
* Fourth, edit the path in `/etc/systemd/system/pitftastro.service` to the path where you checked out the code
* Fifth, enable the `systemd` service.
* Lastly, start the `systemd` service, or reboot.

Quick command list to install:

```shell
git clone https://github.com/awicenec/pitftastro.git
cd pitftastro
sudo pip3 install -r requirements.txt
sudo cp pitftastro/pitftastro.service /etc/systemd/system/
sudo nano /etc/systemd/system/pitftastro.service  # don't forget to change the path!
sudo systemctl daemon-reload
sudo systemctl enable pitftastro
sudo systemctl start pitftastro
```