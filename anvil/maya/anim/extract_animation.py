import pyblish.api


class ExtractAvaAnimation(pyblish.api.InstancePlugin):
    """Produce an alembic of just point positions and normals.

    Positions and normals are preserved, but nothing more,
    for plain and predictable point caches.

    Limitations:
        - Framerange is bound to current maximum range in Maya

    """

    label = "Animation"
    order = pyblish.api.ExtractorOrder
    hosts = ["maya"]
    families = ["anvil.animation"]

    def process(self, instance):
        import os
        import anvil.plugins.publish.utils as utils
        from maya import cmds
        from avalon import maya

        self.log.debug("Loading plug-in..")
        cmds.loadPlugin("AbcExport.mll", quiet=True)

        self.log.info("Extracting animation..")
        dirname = utils.format_staging_dir(
            root=instance.context.data["workspaceDir"],
            time=instance.context.data["time"],
            name=instance.data["name"])

        try:
            os.makedirs(dirname)
        except OSError:
            pass

        filename = "{name}.abc".format(**instance.data)

        out_set = next((
            node for node in instance
            if node.endswith("out_SET")
        ), None)

        if out_set:
            nodes = cmds.sets(out_set, query=True)
        else:
            # Backwards compatibility
            nodes = list(instance)

        self.log.info("nodes: %s" % str(nodes))
        with maya.suspended_refresh():
            maya.export_alembic(
                nodes=nodes,
                file=os.path.join(dirname, filename).replace("\\", "/"),

                frame_range=(instance.data["startFrame"],
                             instance.data["endFrame"]),

                # Include UVs
                write_uv=True,

                # Include Visibility
                write_visibility=True,

                # Include all attributes prefixed with this
                attribute_prefix="mb"
            )

        # Store reference for integration
        if "files" not in instance.data:
            instance.data["files"] = list()

        instance.data["files"].append(filename)
        instance.data["stagingDir"] = dirname

        self.log.info("Extracted {instance} to {dirname}".format(**locals()))
