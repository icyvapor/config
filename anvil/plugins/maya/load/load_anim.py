import avalon.maya


class AbcLoader(avalon.maya.Loader):
    """Specific loader of Alembic for the anvil.animation family"""

    families = ["anvil.animation"]
    representations = ["abc"]

    def process(self, name, namespace, context, data):
        from maya import cmds

        cmds.loadPlugin("AbcImport.mll", quiet=True)

        nodes = cmds.file(
            self.fname,
            namespace=namespace,

            # Prevent identical alembic nodes
            # from being shared.
            sharedReferenceFile=False,

            groupReference=True,
            groupName=namespace + ":" + name,
            reference=True,
            returnNewNodes=True
        )

        self[:] = nodes


class CurvesLoader(avalon.maya.Loader):
    """Specific loader of Curves for the anvil.animation family"""

    families = ["anvil.animation"]
    representations = ["curves"]

    def process(self, name, namespace, context, data):
        from maya import cmds
        from avalon import maya, api

        cmds.loadPlugin("atomImportExport.mll", quiet=True)

        # Load the rig using the RigLoader
        loader = {Loader.__name__: Loader for Loader in
                  api.discover(avalon.maya.Loader)}.get("RigLoader", None)
        if loader is None:
            raise RuntimeError("Unable to find RigLoader")

        rig = context["representation"]["dependencies"][0]
        container = maya.load(loader,
                              rig,
                              name=name,
                              namespace=namespace,

                              # Skip creation of Animation instance
                              data={"post_process": False})

        try:
            control_set = next(
                node for node in cmds.sets(container, query=True)
                if node.endswith("controls_SET")
            )
        except StopIteration:
            raise TypeError("%s is missing controls_SET")

        cmds.select(control_set)
        options = ";".join([
            "",
            "",
            "targetTime=3",
            "option=insert",
            "match=hierarchy",
            "selected=selectedOnly",
            "search=",
            "replace=",
            "prefix=",
            "suffix=",
            "mapFile=",
        ])

        cmds.select(
            control_set,
            replace=True,

            # Support controllers being embedded in
            # additional selection sets.
            noExpand=False
        )

        nodes = cmds.file(
            self.fname,
            i=True,
            type="atomImport",
            renameAll=True,
            namespace=namespace,
            options=options,
            returnNewNodes=True,
        )

        self[:] = nodes + cmds.sets(container, query=True) + [container]

        # Trigger post process only if it's not been set to disabled
        if data.get("post_process", True):
            self._post_process(name, namespace, context, data)

    def _post_process(self, name, namespace, context, data):
        import os
        from maya import cmds
        from avalon import maya, io

        # Task-dependent post-process
        if os.getenv("AVALON_TASK") != "animate":
            return self.log.info(
                "No animation instance created due to task != animate"
            )

        # Find associated rig to these curves
        try:
            dependency = context["representation"]["dependencies"][0]
        except (KeyError, IndexError):
            return self.log.warning("No dependencies found for %s" % name)

        dependency = io.find_one({"_id": io.ObjectId(dependency)})
        _, _, dependency, _ = io.parenthood(dependency)

        # TODO(marcus): We are hardcoding the name "out_SET" here.
        #   Better register this keyword, so that it can be used
        #   elsewhere, such as in the Integrator plug-in,
        #   without duplication.
        output = next(
            (node for node in self
                if node.endswith("out_SET")), None)
        controls = next(
            (node for node in self
                if node.endswith("controls_SET")), None)

        assert output, "No out_SET in rig, this is a bug."
        assert controls, "No controls_SET in rig, this is a bug."

        with maya.maintained_selection():
            cmds.select([output, controls], noExpand=True)

            dependencies = [context["representation"]["_id"]]
            name = "anim" + dependency["name"].title() + "_"

            # TODO(marcus): Hardcoding the family here, better separate this.
            maya.create(
                name=maya.unique_name(name, suffix="_SET"),
                family="anvil.animation",
                options={"useSelection": True},
                data={
                    "dependencies": " ".join(str(d) for d in dependencies)
                })


class HistoryLoader(avalon.maya.Loader):
    """Specific loader of Curves for the anvil.animation family"""

    families = ["anvil.animation"]
    representations = ["history"]

    def process(self, name, namespace, context, data):
        raise NotImplementedError("Can't load history yet.")
