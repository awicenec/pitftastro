#!/usr/bin/env python3

import logging
import sys

import posix_ipc

logger = logging.getLogger("pitftastro.cli")

if len(sys.argv) < 2:
    logger.error("No command specified")
    exit(1)

try:
    mq = posix_ipc.MessageQueue("/pitftastro_ipc")
    mq.block = False
except posix_ipc.PermissionsError:
    mq = None
    logger.error("couldn't open message queue")
    exit(1)

command_line = " ".join(sys.argv[1:])

mq.send(command_line, timeout=10)
