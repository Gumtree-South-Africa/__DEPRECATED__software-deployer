import os
import fnmatch
from datetime import datetime

from deployerlib.command import Command
from deployerlib.exceptions import DeployerException


class Archive(Command):
    """Archive releases"""

    def initialize(self, archivedir, archivedepth=-1, release='', components=[]):
        self.archivedepth = archivedepth
        self.release = release.rstrip('/')
        self.components = components
        return True

    def execute(self):
        if self.archivedir[0] != '/':
            self.log.critical('Archive directory path {0} is not absolute!'.format(self.archivedir))
            return False

        if os.path.isdir(self.archivedir) == False:
            self.log.critical("Archive directory %s does not exist!" % self.archivedir)
            return False

        if self.release or self.components:
            ctime = lambda f: os.stat(os.path.join(self.archivedir, f)).st_ctime
            dlist = [d for d in list(sorted(os.listdir(self.archivedir), key = ctime)) if os.path.isdir(os.path.join(self.archivedir, d))]
            if dlist:
                last_deployed = dlist[-1]
            else:
                # create an empty last_deployed dir:
                last_deployed = datetime.now().strftime('%Y%m%d%H%M%S')
                os.mkdir(os.path.join(self.archivedir, last_deployed))
        else:
            self.log.critical('Either "release" or "components" arguments should be set. Both appear to be empty')
            return False

        if self.components:
            files_in_last_release = os.listdir(os.path.join(self.archivedir, last_deployed))

            new_components = []
            for component in self.components:
                component_base = os.path.basename(component)
                if component_base in files_in_last_release:
                    self.log.info("Component {0} is a part of last release ({1}).".format(component_base, last_deployed))
                else:
                    new_components.append(component)

            if new_components:
                self.log.info("Creating a hotfix snapshot of last deployed release: %s" % last_deployed)
                last_release = last_deployed.split('-hf_')[0]
                prev_hotfixes = sorted([int(hf.split('-hf_')[-1]) for hf in dlist if fnmatch.fnmatchcase(hf,
                    '{0}-hf_[1-9]*'.format(last_release))])
                if prev_hotfixes:
                    highest_prev_hf = prev_hotfixes[-1]
                    new_hotfix_version = highest_prev_hf + 1
                else:
                    new_hotfix_version = 1

                src_dir = os.path.join(self.archivedir, last_deployed)
                dst_dir = os.path.join(self.archivedir, "{0}-hf_{1}".format(last_release, new_hotfix_version))
                last_release_dir = os.path.join(self.archivedir, last_release)

                exclude_opts = []
                components_names = []
                for component in new_components:
                    component_base = os.path.basename(component)
                    component_name = component_base.split("_")[0]
                    exclude_opts.append("--exclude '{0}_*'".format(component_name))
                    components_names.append(component_name)

                self.log.info("Copying {0} to {1}, excluding components {2}.".format(src_dir, dst_dir, ', '.join(components_names)))
                # this also creates dst_dir
                os.system('rsync -a --no-times --size-only {0} --link-dest={1} {1}/ {2}/'.format(' '.join(exclude_opts), src_dir, dst_dir))

                for component in new_components:
                    component_dir = os.path.dirname(component)
                    component_base = os.path.basename(component)
                    component_name = component_base.split("_")[0]
                    self.log.info("Placing newly deployed component {0} to {1}".format(component_name, dst_dir))
                    os.system("rsync -a --no-times --size-only --link-dest={0} {1} {2}/".format(component_dir, component, dst_dir))
            else:
                self.log.info("Not creating a new hotfix snapshot.")

        elif self.release:
            self.log.info("Putting release %s to archive %s" % (self.release, self.archivedir))
            last_deployed_dir = os.path.join(self.archivedir, last_deployed)
            release_base = os.path.basename(self.release)
            os.system('rsync -a --no-times --size-only --link-dest={0} --link-dest={1} {1}/ {2}/'.format(last_deployed_dir, self.release,
                os.path.join(self.archivedir, release_base)))
            os.system('touch {0}'.format(os.path.join(self.archivedir, release_base)))

        # clean archive
        removeList = list(sorted(os.listdir(self.archivedir), key=ctime))[0:-self.archivedepth]
        if len(removeList) > 0:
            self.log.info("Found {0} archived releases/hotfixes to remove.".format(len(removeList)))
            for target in removeList:
                if target:
                    self.log.info('Removing {0} for cleanup.'.format(target))
                    os.system('rm -r {0}'.format(os.path.join(self.archivedir, target)))
        else:
            self.log.info("No archived releases to clean up.")

        return True
