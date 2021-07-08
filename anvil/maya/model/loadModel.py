import avalon.maya


class ModelLoader(avalon.maya.Loader):
    """Load models

    Stores the imported asset in a container named after the asset.

    """

    families = ["anvil.model"]
    representations = ["ma"]

    def process(self, name, namespace, context, data):
        from maya import cmds

        print(self.fname)
        self[:] = cmds.file(
            self.fname,
            namespace=namespace,
            reference=True,
            returnNewNodes=True,
            groupReference=True,
            groupName=namespace + ":" + name
        )

        # Assign default shader to meshes
        meshes = cmds.ls(self, type="mesh")
        cmds.sets(meshes, forceElement="initialShadingGroup")
