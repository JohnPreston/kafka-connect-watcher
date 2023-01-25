#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

from __future__ import annotations

import re


def import_regexes(to_import: list[str]) -> list[re.Pattern]:
    compiled_regexes: list[re.Pattern] = []
    for regex in to_import:
        try:
            re_gex = re.compile(regex)
            compiled_regexes.append(re_gex)
        except Exception as error:
            print(regex)
            print(error)
    return compiled_regexes
