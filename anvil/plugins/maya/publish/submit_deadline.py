import pyblish.api


class AvaSubmitDeadline(pyblish.api.InstancePlugin):
    """Submit available render layers to Deadline

    Renders are submitted to a Deadline Web Service as
    supplied via the environment variable AVALON_DEADLINE

    """

    label = "Submit to Deadline"
    order = pyblish.api.IntegratorOrder
    hosts = ["maya"]
    families = ["anvil.renderlayer"]

    def process(self, instance):
        import os
        import json
        import shutil
        import getpass

        from maya import cmds

        from avalon import api
        from avalon.vendor import requests

        assert "AVALON_DEADLINE" in api.Session, (
            "Environment variable missing: 'AVALON_DEADLINE"
        )

        AVALON_DEADLINE = api.Session["AVALON_DEADLINE"]

        context = instance.context
        workspace = context.data["workspaceDir"]
        fpath = context.data["currentFile"]
        fname = os.path.basename(fpath)
        name, ext = os.path.splitext(fname)
        comment = context.data.get("comment", "")
        dirname = os.path.join(workspace, "renders", name)

        try:
            os.makedirs(dirname)
        except OSError:
            pass

        # E.g. http://192.168.0.1:8082/api/jobs
        url = "{}/api/jobs?JobID=%s".format(AVALON_DEADLINE)

        # Documentation for keys available at:
        # https://docs.thinkboxsoftware.com
        #    /products/deadline/8.0/1_User%20Manual/manual
        #    /manual-submission.html#job-info-file-options
        payload = {
            "JobInfo": {
                # Top-level group name
                "BatchName": fname,

                # Job name, as seen in Monitor
                "Name": "%s - %s" % (fname, instance.name),

                # Arbitrary username, for visualisation in Monitor
                "UserName": getpass.getuser(),

                "Plugin": "MayaBatch",
                "Frames": "{start}-{end}x{step}".format(
                    start=int(instance.data["startFrame"]),
                    end=int(instance.data["endFrame"]),
                    step=int(instance.data["byFrameStep"]),
                ),

                "Comment": comment,

                # Optional, enable double-click to preview rendered
                # frames from Deadline Monitor
                "OutputFilename0": self.preview_fname(instance),
            },
            "PluginInfo": {
                # Input
                "SceneFile": fpath,

                # Output directory and filename
                "OutputFilePath": dirname,
                "OutputFilePrefix": "<RenderLayer>/<RenderLayer>",

                # Mandatory for Deadline
                "Version": cmds.about(version=True),

                # Only render layers are considered renderable in this pipeline
                "UsingRenderLayers": True,

                # Render only this layer
                "RenderLayer": instance.name,

                # Determine which renderer to use from the file itself
                "Renderer": "file",

                # Resolve relative references
                "ProjectPath": workspace,
            },

            # Mandatory for Deadline, may be empty
            "AuxFiles": []
        }

        # Include critical variables with submission
        environment = dict({
            # This will trigger `userSetup.py` on the slave
            # such that proper initialisation happens the same
            # way as it does on a local machine.
            # TODO(marcus): This won't work if the slaves don't
            # have accesss to these paths, such as if slaves are
            # running Linux and the submitter is on Windows.
            "PYTHONPATH": os.getenv("PYTHONPATH", ""),

        }, **api.Session)

        payload["JobInfo"].update({
            "EnvironmentKeyValue%d" % index: "{key}={value}".format(
                key=key,
                value=environment[key]
            ) for index, key in enumerate(environment)
        })

        # Include optional render globals
        payload["JobInfo"].update(
            instance.data.get("renderGlobals", {})
        )

        self.preflight_check(instance)

        self.log.info("Submitting..")
        self.log.info(json.dumps(
            payload, indent=4, sort_keys=True)
        )

        response = requests.post(url, json=payload)

        if response.ok:
            # Write metadata for publish
            fname = os.path.join(dirname, instance.name + ".json")
            data = {
                "submission": payload,
                "session": api.Session,
                "instance": instance.data,
                "jobs": [
                    response.json()
                ],
            }

            with open(fname, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)

        else:
            try:
                shutil.rmtree(dirname)
            except OSError:
                # This is nice-to-have, but not critical to the operation
                pass

            raise Exception(response.text)

    def preview_fname(self, instance):
        """Return outputted filename with #### for padding

        Passing the absolute path to Deadline enables Deadline Monitor
        to provide the user with a Job Output menu option.

        Deadline requires the path to be formatted with # in place of numbers.

        From
            /path/to/render.0000.png
        To
            /path/to/render.####.png

        """

        from maya import cmds

        # We'll need to take tokens into account
        fname = cmds.renderSettings(
            firstImageName=True,
            fullPath=True,
            layer=instance.name
        )[0]

        try:
            # Assume `c:/some/path/filename.0001.exr`
            # TODO(marcus): Bulletproof this, the user may have
            # chosen a different format for the outputted filename.
            fname, padding, suffix = fname.rsplit(".", 2)
            fname = ".".join([fname, "#" * len(padding), suffix])
            self.log.info("Assuming renders end up @ %s" % fname)
        except ValueError:
            fname = ""
            self.log.info("Couldn't figure out where renders go")

        return fname

    def preflight_check(self, instance):
        for key in ("startFrame", "endFrame", "byFrameStep"):
            value = instance.data[key]

            if int(value) == value:
                continue

            self.log.warning(
                "%f=%d was rounded off to nearest integer"
                % (value, int(value))
            )
