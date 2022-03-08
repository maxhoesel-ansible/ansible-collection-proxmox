# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


api_connection_argspec = dict(
    api_host=dict(type="str", required=True),
    api_user=dict(type="str", required=True),
    api_password=dict(type="str", no_log=True),
    validate_certs=dict(type="bool", default=False)
)
