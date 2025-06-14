#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>


from os import cpu_count, environ

NUM_THREADS: int = abs(int(environ.get("CONCURRENT_THREADS", cpu_count())))
if NUM_THREADS <= 0:
    NUM_THREADS = 1
