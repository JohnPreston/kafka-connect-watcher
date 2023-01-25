#!/usr/bin/env sh
#
#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>
#

echo $PATH
exec kafka-connect-watcher "$@"
