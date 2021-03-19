"""
Classes for managing the data processing pipeline.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""

import logging

class Pipeline:
    """
    Class for controlling the state of the data processing pipeline.
    """

    def __init__(self, pipeline_state_listeners):
        self.pipeline_state_listeners = pipeline_state_listeners
        self.logger = logging.getLogger(self.__class__.__name__)

    def start(self):
        """
        Register the start of the pipeline processing. The PipelineStateListeners will be notified of this event in the
        order in which they were registered.
        """
        self.logger.debug('Starting.')
        for listener in self.pipeline_state_listeners:
            listener.on_pipeline_start()

    def stop(self):
        """
        Register the end of the pipeline processing. The PipelineStateListeners will be notified of this event in the
        order in which they were registered.
        """
        self.logger.debug('Stopping.')
        for listener in self.pipeline_state_listeners:
            listener.on_pipeline_stop()

########################################################################################################################

class PipelineStateListener:

    def on_pipeline_start(self):
        """
        Invoked by the Pipeline when it receives the 'start' instruction.
        """
        pass

    def on_pipeline_stop(self):
        """
        Invoked by the Pipeline when it receives the 'stop' instruction.
        """
        pass
