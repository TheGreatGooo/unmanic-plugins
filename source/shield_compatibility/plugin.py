#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               yajrendrag <yajdude@gmail.com>, thegreatgooo <thegreatgooo@gmail.com>
    Date:                     16 Feb 2023, (12:02 AM)

    Copyright:
        Copyright (C) 2023 Jay Gardner

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""
import logging
import os

from unmanic.libs.unplugins.settings import PluginSettings

from ignore_files_based_on_metadata.lib.ffmpeg import Probe

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.shield_compatibility")


class Settings(PluginSettings):
    settings = {
    }
    form_settings = {
    }


def file_has_metadata(path, probe_streams, probe_format, metadata_key, metadata_value):
    """
    Check if the file contains disallowed search metadata

    :return:
    """

    # Check if stream or format components contain disallowed metadata
    streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "video"]
    file_has_metadata_key = [streams[i] for i in range(0, len(streams)) if metadata_key in streams[i] and metadata_value in streams[i][metadata_key]]
    probe_format_d = {k:v for  (k, v) in probe_format.items() if type(v) is dict}
    probe_format_kv = {k:v for  (k, v) in probe_format.items() if type(v) is not dict}
    for v in probe_format_d.values():
        probe_format_kv.update(v)
    file_has_metadata_key_fmt = [(k, v) for (k, v) in probe_format_kv.items() if (metadata_key in k.lower() and metadata_value in v)]

    # Check if video, audio, or attachement stream tags contain disallowed metadata
    attachment_streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "attachment"]
    try:
        probe_as_tags_kv = {k:v for i in range(0, len(attachment_streams)) for (k, v) in attachment_streams[i]["tags"].items() if type(v) is not dict}
        file_has_metadata_key_ast = [(k, v) for (k, v) in probe_as_tags_kv.items() if (metadata_key in k.lower() and metadata_value in v)]
    except KeyError:
        file_has_metadata_key_ast = ""

    video_streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "video"]
    try:
        probe_vs_tags_kv = {k:v for i in range(0, len(video_streams)) for (k, v) in video_streams[i]["tags"].items() if type(v) is not dict}
        file_has_metadata_key_vst = [(k, v) for (k, v) in probe_vs_tags_kv.items() if (metadata_key in k.lower() and metadata_value in v)]
    except KeyError:
        file_has_metadata_key_vst = ""

    audio_streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio"]
    try:
        probe_aus_tags_kv = {k:v for i in range(0, len(audio_streams)) for (k, v) in audio_streams[i]["tags"].items() if type(v) is not dict}
        file_has_metadata_key_aust = [(k, v) for (k, v) in probe_aus_tags_kv.items() if (metadata_key in k.lower() and metadata_value in v)]
    except KeyError:
        file_has_metadata_key_aust = ""

    if file_has_metadata_key or file_has_metadata_key_fmt or file_has_metadata_key_ast or file_has_metadata_key_vst or file_has_metadata_key_aust:
        logger.debug("File '{}' contains metadata '{}': '{}'.".format(path, metadata_key, metadata_value))
        return True

    logger.debug("File '{}' does not contain metadata '{}': '{}'.".format(path, metadata_key, metadata_value))
    return False


def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.

    :param data:
    :return:

    """

    # Get the path to the file
    abspath = data.get('path')

    # Configure settings object
    settings = Settings(library_id=data.get('library_id'))

    #skip h.264 8bit
    #skip hevc 8bit

    # initialize Probe
    probe_data=Probe(logger, allowed_mimetypes=['video'])

    # Get stream data from probe
    if probe_data.file(abspath):
        probe_streams=probe_data.get_probe()["streams"]
        probe_format = probe_data.get_probe()["format"]
        is_hevc = file_has_metadata(abspath, probe_streams, probe_format, "codec_name", "hevc")
        is_h264 = file_has_metadata(abspath, probe_streams, probe_format, "codec_name", "h264")
        is_ten_bit = file_has_metadata(abspath, probe_streams, probe_format, "pix_fmt", "yuv420p10le")
        if (is_hevc or is_h264) and not is_ten_bit :
            data['add_file_to_pending_tasks'] = False
    else:
        logger.debug("Probe data failed - Blocking everything.")
        data['add_file_to_pending_tasks'] = False
