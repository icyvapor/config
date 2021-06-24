import pyblish.api


class ValidateAvaFrameRange(pyblish.api.InstancePlugin):
    """Animation should normally be published with the range for a shot"""

    label = "Frame Range"
    order = pyblish.api.ValidatorOrder
    hosts = ["maya"]
    optional = True
    families = [
        "anvil.animation",
    ]

    def process(self, instance):
        import os

        instance_in = str(int(instance.data["startFrame"]))
        instance_out = str(int(instance.data["endFrame"]))

        try:
            global_in = os.environ["AVALON_EDIT_IN"]
            global_out = os.environ["AVALON_EDIT_OUT"]
        except KeyError:
            return self.log.info("No edit information available.")

        instance_range = "-".join([instance_in, instance_out])
        global_range = "-".join([global_in, global_out])

        assert instance_range == global_range, (
            "%s != %s - Animation range may be invalid" % (
                instance_range, global_range
            )
        )
