"""Real FoodVisionProvider adapter (provider still TBD; rename to vision_<name>.py once chosen).

TODO: resize with Pillow (max 1024 px, JPEG), send, validate the answer with `VisionResult`, retry
once on timeout, never persist or log the image. Not wired in the container yet.
"""
