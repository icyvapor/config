import pyblish.api


class ExtractAvaLookdev(pyblish.api.InstancePlugin):
    """Export shaders for rendering

    Shaders are associated with an "mdID" attribute on each *transform* node.
    The extracted file is then given the name of the shader, and thereafter
    a relationship is created between a mesh and a file on disk.

    """

    label = "Lookdev"
    order = pyblish.api.ExtractorOrder
    hosts = ["maya"]
    families = ["anvil.lookdev"]

    def process(self, instance):
        import os
        import json
        import anvil.plugins.publish.utils as utils

        from maya import cmds

        from avalon import maya
        from anvil.maya import lib

        dirname = utils.format_staging_dir(
            root=instance.context.data["workspaceDir"],
            time=instance.context.data["time"],
            name=instance.data["name"])

        try:
            os.makedirs(dirname)
        except OSError:
            pass

        filename = "{name}.json".format(**instance.data)

        path = os.path.join(dirname, filename)

        self.log.info("Serialising shaders..")
        relationships = lib.serialise_shaders(instance)

        self.log.info("Extracting serialisation..")
        with open(path, "w") as f:
            json.dump(
                relationships,
                f,

                # This makes the output human-readable,
                # by padding lines to look visually pleasing.
                indent=4
            )

        # Store reference for integration
        if "files" not in instance.data:
            instance.data["files"] = list()

        instance.data["files"].append(filename)

        # Write individual shaders
        # TODO(marcus): How about exporting 1 scene, and
        # maintaining a reference to the shader node name,
        # as opposed to the file?
        self.log.info("Extracting shaders..")
        filename = "{name}.ma".format(**instance.data)
        path = os.path.join(dirname, filename)

        with maya.maintained_selection(), maya.without_extension():
            cmds.select(relationships.keys(), replace=True, noExpand=True)
            cmds.file(path,
                      force=True,
                      options="v=0;",
                      type="mayaAscii",
                      preserveReferences=False,
                      exportSelected=True,
                      constructionHistory=False)

        instance.data["files"].append(filename)
        instance.data["stagingDir"] = dirname

        self.log.info("Extracted {instance} to {path}".format(**locals()))
