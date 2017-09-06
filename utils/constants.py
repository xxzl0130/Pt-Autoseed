# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import time

TABLE_INFO_LIST = "info_list"
TABLE_SEED_LIST = "seed_list"


def period_f(func, sleep_time):
    while True:
        func()
        time.sleep(sleep_time)