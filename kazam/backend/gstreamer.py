# -*- coding: utf-8 -*-
#
#       gstreamer.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import os
import logging
logger = logging.getLogger("GStreamer")

import tempfile
import multiprocessing

#
# This needs to be set before we load GStreamer modules!
#
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
os.putenv("GST_DEBUG_DUMP_DOT_DIR", "/tmp")

from gi.repository import GObject, Gst

from kazam.backend.prefs import *
from kazam.backend.constants import *

GObject.threads_init()
Gst.init(None)
if prefs.debug:
    Gst.debug_set_active(True)
else:
    Gst.debug_set_active(False)


class Screencast(GObject.GObject):
    __gsignals__ = {"flush-done": (GObject.SIGNAL_RUN_LAST,
                    None,
                    (),),
                    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.temp_fh = tempfile.mkstemp(prefix="kazam_", dir=prefs.video_dest, suffix=".movie")
        self.tempfile = self.temp_fh[1]
        self.muxer_tempfile = "{0}.mux".format(self.tempfile)
        self.pipeline = Gst.Pipeline()
        self.area = None
        self.xid = None
        self.crop_vid = False

    def setup_sources(self,
                      video_source,
                      audio_source,
                      audio2_source,
                      area,
                      xid):

        # Get the number of cores available then use all except one for encoding
        self.cores = multiprocessing.cpu_count()

        if self.cores > 1:
            self.cores -= 1

        self.audio_source = audio_source
        self.audio2_source = audio2_source
        self.video_source = video_source
        self.area = area
        self.xid = xid

        logger.debug("Audio_source : {0}".format(audio_source))
        logger.debug("Audio2_source : {0}".format(audio2_source))
        logger.debug("Video_source: {0}".format(video_source))
        logger.debug("Xid: {0}".format(xid))
        logger.debug("Area: {0}".format(area))

        logger.debug("Capture Cursor: {0}".format(prefs.capture_cursor))
        logger.debug("Framerate : {0}".format(prefs.framerate))

        if self.video_source or self.area:
            self.setup_video_source()

        self.setup_audio_sources()

        self.setup_filesink()
        self.setup_pipeline()
        self.setup_links()

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def setup_video_source(self):

        if prefs.test:
            self.videosrc = Gst.ElementFactory.make("videotestsrc", "video_src")
            self.videosrc.set_property("pattern", "smpte")
        else:
            self.videosrc = Gst.ElementFactory.make("ximagesrc", "video_src")

        if self.area:
            logger.debug("Capturing area.")
            startx = self.area[0] if self.area[0] > 0 else 0
            starty = self.area[1] if self.area[1] > 0 else 0
            endx = self.area[2]
            endy = self.area[3]
        else:
            startx = self.video_source['x']
            starty = self.video_source['y']
            width = self.video_source['width']
            height = self.video_source['height']
            endx = startx + width - 1
            endy = starty + height - 1

        #
        # H264 requirement is that video dimensions are divisible by 2.
        # If they are not, we have to get rid of that extra pixel.
        #
        if not abs(startx - endx) % 2 and prefs.codec == CODEC_H264:
            endx -= 1

        if not abs(starty - endy) % 2 and prefs.codec == CODEC_H264:
            endy -= 1

        logger.debug("Coordinates SX: {0} SY: {1} EX: {2} EY: {3}".format(startx, starty, endx, endy))

        if prefs.test:
            logger.info("Using test signal instead of screen capture.")
            self.vid_caps = Gst.caps_from_string("video/x-raw, framerate={0}/1".format(
                  int(prefs.framerate)))
            self.vid_caps_filter = Gst.ElementFactory.make("capsfilter", "vid_filter")
            self.vid_caps_filter.set_property("caps", self.vid_caps)
        else:
            logger.debug("testing for xid: {0}".format(self.xid))
            if self.xid:   # xid was passed, so we have to capture a single window.
                logger.debug("Capturing Window: {0} {1}".format(self.xid, prefs.xid_geometry))
                self.videosrc.set_property("xid", self.xid)

                if prefs.codec == CODEC_H264:
                    self.videocrop = Gst.ElementFactory.make("videocrop", "cropper")
                    if prefs.xid_geometry[2] % 2:
                        self.videocrop.set_property("left", 1)
                        self.crop_vid = True
                    if prefs.xid_geometry[3] % 2:
                        self.videocrop.set_property("bottom", 1)
                        self.crop_vid = True
            else:
                self.videosrc.set_property("startx", startx)
                self.videosrc.set_property("starty", starty)
                self.videosrc.set_property("endx", endx)
                self.videosrc.set_property("endy", endy)

            self.videosrc.set_property("use-damage", False)
            self.videosrc.set_property("show-pointer", prefs.capture_cursor)

            self.vid_caps = Gst.caps_from_string("video/x-raw, framerate={0}/1".format(int(prefs.framerate)))
            self.vid_caps_filter = Gst.ElementFactory.make("capsfilter", "vid_filter")
            self.vid_caps_filter.set_property("caps", self.vid_caps)

        self.videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
        self.videorate = Gst.ElementFactory.make("videorate", "video_rate")

        logger.debug("Codec: {0}".format(CODEC_LIST[prefs.codec][2]))

        if prefs.codec is not CODEC_RAW:
            self.videnc = Gst.ElementFactory.make(CODEC_LIST[prefs.codec][1], "video_encoder")

        if prefs.codec == CODEC_RAW:
            self.mux = Gst.ElementFactory.make("avimux", "muxer")
        elif prefs.codec == CODEC_VP8:
            self.videnc.set_property("cpu-used", 2)
            self.videnc.set_property("end-usage", "vbr")
            self.videnc.set_property("target-bitrate", 800000000)
            self.videnc.set_property("static-threshold", 1000)
            self.videnc.set_property("token-partitions", 2)
            self.videnc.set_property("max-quantizer", 30)
            self.videnc.set_property("threads", self.cores)
            self.mux = Gst.ElementFactory.make("webmmux", "muxer")
        elif prefs.codec == CODEC_H264:
            self.videnc.set_property("speed-preset", "ultrafast")
            self.videnc.set_property("pass", 4)
            self.videnc.set_property("quantizer", 15)
            #
            # x264enc supports maximum of four cores
            #
            self.videnc.set_property("threads", self.cores if self.cores <= 4 else 4)
            self.mux = Gst.ElementFactory.make("mp4mux", "muxer")
            self.mux.set_property("faststart", 1)
            self.mux.set_property("faststart-file", self.muxer_tempfile)
            self.mux.set_property("streamable", 1)
        elif prefs.codec == CODEC_HUFF:
            self.mux = Gst.ElementFactory.make("avimux", "muxer")
            self.videnc.set_property("bitrate", 500000)
        elif prefs.codec == CODEC_JPEG:
            self.mux = Gst.ElementFactory.make("avimux", "muxer")

        self.vid_in_queue = Gst.ElementFactory.make("queue", "queue_v1")
        self.vid_out_queue = Gst.ElementFactory.make("queue", "queue_v2")

    def setup_audio_sources(self):
        if self.audio_source or self.audio2_source:
            logger.debug("Setup audio elements.")
            self.aud_out_queue = Gst.ElementFactory.make("queue", "queue_a_out")
            self.audioconv = Gst.ElementFactory.make("audioconvert", "audio_conv")
            if prefs.codec == CODEC_VP8:
                self.audioenc = Gst.ElementFactory.make("vorbisenc", "audio_encoder")
                self.audioenc.set_property("quality", 1)
            else:
                self.audioenc = Gst.ElementFactory.make("lamemp3enc", "audio_encoder")
                self.audioenc.set_property("quality", 0)

        if self.audio_source:
            logger.debug("Audio1 Source:\n  {0}".format(self.audio_source))
            self.audiosrc = Gst.ElementFactory.make("pulsesrc", "audio_src")
            self.audiosrc.set_property("device", self.audio_source)
            self.aud_caps = Gst.caps_from_string("audio/x-raw")
            self.aud_caps_filter = Gst.ElementFactory.make("capsfilter", "aud_filter")
            self.aud_caps_filter.set_property("caps", self.aud_caps)

            self.aud_in_queue = Gst.ElementFactory.make("queue", "queue_a_in")

        if self.audio2_source:
            logger.debug("Audio2 Source:\n  {0}".format(self.audio2_source))
            self.audio2src = Gst.ElementFactory.make("pulsesrc", "audio2_src")
            self.audio2src.set_property("device", self.audio2_source)
            self.aud2_caps = Gst.caps_from_string("audio/x-raw")
            self.aud2_caps_filter = Gst.ElementFactory.make("capsfilter", "aud2_filter")
            self.aud2_caps_filter.set_property("caps", self.aud2_caps)
            self.aud2_in_queue = Gst.ElementFactory.make("queue", "queue_a2_in")
            self.audio2conv = Gst.ElementFactory.make("audioconvert", "audio2_conv")

        if self.audio_source and self.audio2_source:
            self.audiomixer = Gst.ElementFactory.make("adder", "audiomixer")

    def setup_filesink(self):
        logger.debug("Filesink: {0}".format(self.tempfile))
        self.sink = Gst.ElementFactory.make("filesink", "sink")
        self.sink.set_property("location", self.tempfile)
        self.file_queue = Gst.ElementFactory.make("queue", "queue_file")

    #
    # One day, this horrific code will be optimised... I promise!
    #
    def setup_pipeline(self):
        #
        # Behold, setup the master pipeline
        #
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.vid_in_queue)
        if self.crop_vid:
            self.pipeline.add(self.videocrop)
        self.pipeline.add(self.videorate)
        self.pipeline.add(self.vid_caps_filter)
        self.pipeline.add(self.videoconvert)
        self.pipeline.add(self.vid_out_queue)
        self.pipeline.add(self.file_queue)

        if prefs.codec is not CODEC_RAW:
            self.pipeline.add(self.videnc)

        if self.audio_source or self.audio2_source:
            self.pipeline.add(self.audioconv)
            self.pipeline.add(self.audioenc)
            self.pipeline.add(self.aud_out_queue)

        if self.audio_source:
            self.pipeline.add(self.audiosrc)
            self.pipeline.add(self.aud_in_queue)
            self.pipeline.add(self.aud_caps_filter)

        if self.audio2_source:
            self.pipeline.add(self.audio2src)
            self.pipeline.add(self.aud2_in_queue)
            self.pipeline.add(self.aud2_caps_filter)

        if self.audio_source and self.audio2_source:
            self.pipeline.add(self.audiomixer)

        self.pipeline.add(self.mux)
        self.pipeline.add(self.sink)

    # gst-launch-1.0 -e ximagesrc endx=1919 endy=1079 use-damage=false show-pointer=true ! \
    #   queue ! videorate ! video/x-raw,framerate=15/1 ! videoconvert ! \
    #   vp8enc end-usage=vbr target-bitrate=800000000 threads=3 static-threshold=1000 \
    #     token-partitions=2 max-quantizer=30 ! queue name=before_mux ! webmmux name=mux ! \
    #   queue ! filesink location="test-videorate.webm"

    def setup_links(self):
        # Connect everything together
        self.videosrc.link(self.vid_in_queue)
        if self.crop_vid:
            self.vid_in_queue.link(self.videocrop)
            self.videocrop.link(self.videorate)
        else:
            self.vid_in_queue.link(self.videorate)
        self.videorate.link(self.vid_caps_filter)
        self.vid_caps_filter.link(self.videoconvert)
        if prefs.codec is CODEC_RAW:
            self.videoconvert.link(self.vid_out_queue)
            logger.debug("Linking RAW Video")
        else:
            logger.debug("Linking Video")
            self.videoconvert.link(self.videnc)
            self.videnc.link(self.vid_out_queue)

        self.vid_out_queue.link(self.mux)

        if self.audio_source and self.audio2_source:
            logger.debug("Linking Audio")
            ret = self.audiosrc.link(self.aud_in_queue)
            logger.debug(" Link audiosrc -> aud_in_queue: %s" % ret)
            ret = self.aud_in_queue.link(self.aud_caps_filter)
            logger.debug(" Link aud_in_queue -> aud_caps_filter: %s" % ret)

            logger.debug("Linking Audio2")
            # Link first audio source to mixer
            ret = self.aud_caps_filter.link(self.audiomixer)
            logger.debug(" Link aud_caps_filter -> audiomixer: %s" % ret)

            # Link second audio source to mixer
            ret = self.audio2src.link(self.aud2_in_queue)
            logger.debug(" Link audio2src -> aud2_in_queue: %s" % ret)
            ret = self.aud2_in_queue.link(self.aud2_caps_filter)
            logger.debug(" Link aud2_in_queue -> aud2_caps_filter: %s" % ret)
            ret = self.aud2_caps_filter.link(self.audiomixer)
            logger.debug(" Link aud2_caps_filter -> audiomixer: %s" % ret)

            # Link mixer to audio convert
            ret = self.audiomixer.link(self.audioconv)
            logger.debug(" Link audiomixer -> audioconv: %s" % ret)

        elif self.audio_source:

            logger.debug("Linking Audio")
            ret = self.audiosrc.link(self.aud_in_queue)
            logger.debug(" Link audiosrc -> aud_in_queue: %s" % ret)
            ret = self.aud_in_queue.link(self.aud_caps_filter)
            logger.debug(" Link aud_in_queue -> aud_caps_filter: %s" % ret)

            # Link first audio source to audio convert
            ret = self.aud_caps_filter.link(self.audioconv)
            logger.debug(" Link aud_caps_filter -> audioconv: %s" % ret)

        elif self.audio2_source:
            # Link second audio source to mixer
            ret = self.audio2src.link(self.aud2_in_queue)
            logger.debug(" Link audio2src -> aud2_in_queue: %s" % ret)
            ret = self.aud2_in_queue.link(self.aud2_caps_filter)
            logger.debug(" Link aud2_in_queue -> aud2_caps_filter: %s" % ret)

            # Link second audio source to audio convert
            ret = self.aud2_caps_filter.link(self.audioconv)
            logger.debug(" Link aud2_caps_filter -> audioconv: %s" % ret)

        if self.audio_source or self.audio2_source:
            # Link audio to muxer
            ret = self.audioconv.link(self.audioenc)
            logger.debug("Link audioconv -> audioenc: %s" % ret)
            ret = self.audioenc.link(self.aud_out_queue)
            logger.debug("Link audioenc -> aud_out_queue: %s" % ret)
            ret = self.aud_out_queue.link(self.mux)
            logger.debug("Link aud_out_queue -> mux: %s" % ret)

        ret = self.mux.link(self.file_queue)
        logger.debug("Link mux -> file queue: %s" % ret)
        ret = self.file_queue.link(self.sink)
        logger.debug("Link file queue -> sink: %s" % ret)

    def start_recording(self):
        logger.debug("Setting STATE_PLAYING")
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause_recording(self):
        logger.debug("Setting STATE_PAUSED")
        self.pipeline.set_state(Gst.State.PAUSED)

    def unpause_recording(self):
        logger.debug("Setting STATE_PLAYING - UNPAUSE")
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_recording(self):
        logger.debug("Sending new EOS event")
        self.pipeline.send_event(Gst.Event.new_eos())

    def get_tempfile(self):
        return self.tempfile

    def get_audio_recorded(self):
        return self.audio

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            logger.debug("Received EOS, setting pipeline to NULL.")
            self.pipeline.set_state(Gst.State.NULL)
            logger.debug("Emitting flush-done.")
            self.emit("flush-done")
        elif t == Gst.MessageType.ERROR:
            logger.debug("Received an error message: %s", message.parse_error()[1])
