import abc
import os
import shutil

from gitfails import utils
from gitfails.actions import (
    commit_files,
    create_branch_and_checkout,
    create_file,
    create_file_and_commit,
    create_repo,
    modify_file,
    modify_file_and_commit,
)


class Scenario(abc.ABC):
    def __init__(self, dirpath, overwrite=False):
        self.dirpath = dirpath
        if overwrite:
            if os.path.exists(self.dirpath):
                shutil.rmtree(self.dirpath)

    @abc.abstractmethod
    def construct(self):
        raise NotImplementedError


class TwoFeatureBranches(Scenario):
    """
    A git repo with a `main` branch and two feature branches, A and B.

    Suppose a commit on A is required to make progress on B,
    so either B is rebased on A, or the commit is cherry-picked from A to B.
    Development on both branches then continues, until A is merged to main.

    When B is eventually merged to main, what happens to the commits originally on A
    that were 'added' on B (by either rebasing or cherry picking)?
    """

    def construct(self):
        """ """
        author = "Developer 1"
        repo_dirpath = self.dirpath / "repo"
        repo = create_repo(repo_dirpath)

        # Create a file on the main branch and commit.
        create_file_and_commit(
            repo,
            author,
            filename="file1.txt",
            content="Initial content",
            message="Initial commit",
        )

        # Create branch A, add a file, and commit.
        create_branch_and_checkout(repo, "A")
        create_file_and_commit(
            repo,
            author,
            filename="file2.txt",
            content="Content from branch A",
            message="Commit on branch A",
        )

        # Switch back to main, create branch B, add a file, and commit.
        create_branch_and_checkout(repo, "main")
        create_branch_and_checkout(repo, "B")
        create_file_and_commit(
            repo,
            author,
            filename="file3.txt",
            content="Content from branch B",
            message="Commit on branch B",
        )

        # Switch back to the main branch.
        create_branch_and_checkout(repo, "main")


class ForcePushSharedBranch(Scenario):
    """
    A remote repo with an existing dev branch is cloned by two developers.
    Their local dev branches diverge after each makes new commits to their local dev branches.
    One of them rebases their local dev branch on main and then force pushes to the remote.

    How can the second developer update their local dev branch after the rebase
    to incorporate the first developer's changes, and then contribute their own changes?
    """

    def construct(self):
        # Set up the remote/origin repo.
        origin_repo = create_repo(self.dirpath / "origin")
        create_file_and_commit(
            origin_repo,
            author="maintainers",
            filename="file1.txt",
            content="Initial content",
            message="Initial commit",
        )
        modify_file_and_commit(
            origin_repo,
            author="maintainers",
            filename="file1.txt",
            content="Modified content",
            message="Second commit",
            overwrite=True,
        )

        # Clone the origin repo to represent local repos of two developers.
        bad_dev_repo = origin_repo.clone(self.dirpath / "bad_dev")
        good_dev_repo = origin_repo.clone(self.dirpath / "good_dev")

        # The bad dev creates a `dev` branch, makes a commit, and pushes to the origin.
        create_branch_and_checkout(bad_dev_repo, "dev")
        create_file_and_commit(
            bad_dev_repo,
            author="bad-dev",
            filename="file2.txt",
            content="some new feature",
            message="add new feature",
        )
        bad_dev_repo.remotes.origin.push("dev")

        # Create a new commit directly on `main` in the origin.
        # (this represents ongoing changes from, e.g., merged PRs)
        modify_file_and_commit(
            origin_repo,
            author="maintainers",
            filename="file1.txt",
            content="Modified content again",
            message="Third commit",
            overwrite=True,
        )

        # Update the main branch in both dev repos.
        good_dev_repo.git.checkout("main")
        good_dev_repo.remotes.origin.pull("main")
        bad_dev_repo.git.checkout("main")
        bad_dev_repo.remotes.origin.pull("main")

        # The good dev fetches the dev branch and adds a new commit to modify the feature.
        good_dev_repo.remotes.origin.fetch()
        good_dev_repo.git.checkout("dev")
        modify_file_and_commit(
            good_dev_repo,
            author="good-dev",
            filename="file2.txt",
            content="some modified new feature",
            message="modified new feature",
            overwrite=True,
        )

        # The bad dev rebases their dev branch on the updated main branch and force-pushes it.
        bad_dev_repo.git.checkout("dev")
        bad_dev_repo.git.rebase("main")
        bad_dev_repo.remotes.origin.push("dev", force=True)

        # The good dev fetches and checkouts out the dev branch,
        # which because of the force-push has now diverged from the remote dev branch.
        good_dev_repo.remotes.origin.fetch()
        good_dev_repo.git.checkout("dev")


class DivergedCommitHistories(Scenario):
    """
    Suppose there are two remote repos that, initially, have the same commit history.
    One repo resembles a fork of the other, so we call the first repo the 'upstream'
    and the second repo the 'fork', though there is no explicit relationship between the two.

    At some point, the commit histories of the two repos diverge when different developers
    push a series of different commits to each repo.
    However, most or even all of the changes made to the upstream repo are also made to the fork,
    but in a different order and with some additional changes mixed in.

    Later, we want to diff the two repos to see what changes were made to the upstream repo
    that were not made to the fork, and vice versa.
    If the fork includes all of the changes made to the upstream,
    then we expect the diff to be empty and we can say that the fork is up to date
    even though it has a different commit history.

    We also want to understand how git will handle merging the upstream into the fork
    (or vice versa).

    For example, suppose a line or file was added in the fork, but not in the upstream.
    If the upstream is merged into the fork, will the new line or file be deleted? If not, why not?

    Anecdotally, it is possible for the fork to be up-to-date with the upstream
    but for merge conflicts to still occur when merging the upstream into the fork
    (even though the eventual merge is a no-op).
    """

    def construct(self):
        """
        Create two repos, one upstream and one fork, with diverging commit histories.
        """
        upstream_repo = create_repo(self.dirpath / "upstream")

        # Create the readme as the first commit.
        create_file_and_commit(
            upstream_repo,
            author="original-dev",
            filename="README.md",
            content="This is the readme",
            message="Initial commit",
        )

        # Add a script.
        create_file_and_commit(
            upstream_repo,
            author="original-dev",
            filename="script.py",
            content="inital content",
            message="add script.py",
        )

        # Clone the upstream to create a fork and, for clarity, rename the remote to 'upstream'.
        forked_repo = upstream_repo.clone(self.dirpath / "fork")
        forked_repo.git.remote("rename", "origin", "upstream")

        # Now an external dev adds a new line to the script in the upstream.
        new_line_added_by_external_dev = "new line added by external dev"
        modify_file_and_commit(
            upstream_repo,
            author="external-dev",
            filename="script.py",
            content=new_line_added_by_external_dev,
            message="modify script.py",
            overwrite=False,
        )

        # Subsequently, an internal dev modifies the script in the fork
        # by adding the line added in the upstream and also another new line.
        # (nb the same result is obtained if these two lines are added in separate commits.)
        internal_addition_to_script = "\n".join(
            [
                "new line added by internal dev",
                new_line_added_by_external_dev,
            ]
        )
        modify_file_and_commit(
            forked_repo,
            author="internal-dev",
            filename="script.py",
            content=internal_addition_to_script,
            message="modify script.py",
            overwrite=False,
        )

        # Now fetch the upstream in the fork and attempt to merge
        # the upstream main into the fork main; a merge conflict should result
        # because the commit histories of the fork and upstream have diverged,
        # so git has no way to recognize that the fork is only ahead, not behind, the upstream.
        forked_repo.remotes.upstream.fetch()
        forked_repo.git.checkout("main")
        forked_repo.git.merge("upstream/main", "--no-commit", "--no-ff")
