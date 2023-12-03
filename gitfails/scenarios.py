import abc
import os
import shutil

from gitfails import utils
from gitfails.actions import create_branch_and_checkout, create_file_and_commit, create_repo


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
    '''
    A git repo with a `main` branch and two feature branches, A and B.

    Suppose a commit on A is required to make progress on B,
    so either B is rebased on A, or the commit is cherry-picked from A to B.
    Development on both branches then continues, until A is merged to main.

    When B is eventually merged to main, what happens to the commits originally on A
    that were 'added' on B (by either rebasing or cherry picking)?
    '''

    def construct(self):
        ''' '''
        author = 'Developer 1'
        repo_dirpath = self.dirpath / 'repo'
        repo = create_repo(repo_dirpath)

        # create a file on the main branch and commit
        create_file_and_commit(
            repo,
            author,
            filename='file1.txt',
            content='Initial content',
            message='Initial commit',
        )

        # create branch A, add a file, and commit
        create_branch_and_checkout(repo, 'A')
        create_file_and_commit(
            repo,
            author,
            filename='file2.txt',
            content='Content from branch A',
            message='Commit on branch A',
        )

        # switch back to main, create branch B, add a file, and commit
        create_branch_and_checkout(repo, 'main')
        create_branch_and_checkout(repo, 'B')
        create_file_and_commit(
            repo,
            author,
            filename='file3.txt',
            content='Content from branch B',
            message='Commit on branch B',
        )

        # switch back to the main branch
        create_branch_and_checkout(repo, 'main')


class ForcePushSharedBranch(Scenario):
    '''
    A remote repo with an existing dev branch is cloned by two developers.
    Their local dev branches diverge after each makes new commits to their local dev branches.
    One of them rebases their local dev branch on main and then force pushes to the remote.

    How can the second developer update their local dev branch after the rebase
    to incorporate the first developer's changes, and then contribute their own changes?
    '''

    def construct(self):

        # set up the remote/origin repo
        origin_repo = create_repo(self.dirpath / 'origin')
        create_file_and_commit(
            origin_repo,
            author='maintainers',
            filename='file1.txt',
            content='Initial content',
            message='Initial commit',
        )
        create_file_and_commit(
            origin_repo,
            author='maintainers',
            filename='file1.txt',
            content='Modified content',
            message='Second commit',
            overwrite=True,
        )

        # clone the origin repo to represent local repos of two developers
        bad_dev_repo = origin_repo.clone(self.dirpath / 'bad_dev')
        good_dev_repo = origin_repo.clone(self.dirpath / 'good_dev')

        # the bad dev creates a `dev` branch, makes a commit, and pushes to the origin
        create_branch_and_checkout(bad_dev_repo, 'dev')
        create_file_and_commit(
            bad_dev_repo,
            author='bad-dev',
            filename='file2.txt',
            content='some new feature',
            message='add new feature',
        )
        bad_dev_repo.remotes.origin.push('dev')

        # create a new commit directly on `main` in the origin
        # (this represents ongoing changes from, e.g., merged PRs)
        create_file_and_commit(
            origin_repo,
            author='maintainers',
            filename='file1.txt',
            content='Modified content again',
            message='Third commit',
            overwrite=True,
        )

        # update the main branch in both dev repos
        good_dev_repo.git.checkout('main')
        good_dev_repo.remotes.origin.pull('main')
        bad_dev_repo.git.checkout('main')
        bad_dev_repo.remotes.origin.pull('main')

        # the good dev fetches the dev branch and adds a new commit to modify the feature
        good_dev_repo.remotes.origin.fetch()
        good_dev_repo.git.checkout('dev')
        create_file_and_commit(
            good_dev_repo,
            author='good-dev',
            filename='file2.txt',
            content='some modified new feature',
            message='modified new feature',
            overwrite=True,
        )

        # the bad dev rebases their dev branch on the updated main branch and force-pushes it
        bad_dev_repo.git.checkout('dev')
        bad_dev_repo.git.rebase('main')
        bad_dev_repo.remotes.origin.push('dev', force=True)

        # the good dev fetches and checkouts out the dev branch
        # which because of the force-push has now diverged from the remote dev branch
        good_dev_repo.remotes.origin.fetch()
        good_dev_repo.git.checkout('dev')


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

    One specific question: suppose a line or file was added in the fork,
    but not in the upstream. If the upstream is merged into the fork,
    will the new line or file be deleted? If not, why not?

    Anecdotally, it is possible for the fork to be up-to-date with the upstream
    but for merge conflicts to still occur when merging the upstream into the fork
    (even though the eventual merge is a no-op).
    """

    def construct(self):
        # Create the upstream repo and add initial commits
        upstream_repo = create_repo(self.dirpath / 'upstream')
        self._add_commits(
            upstream_repo,
            author='original-dev',
            num_commits=3,
            filename_prefix='some_file',
        )

        # Clone the upstream to create a fork
        fork_repo = upstream_repo.clone(self.dirpath / 'fork')

        # Add diverging commits to upstream
        self._add_commits(
            upstream_repo,
            author='external-dev',
            num_commits=3,
            filename_prefix='some_new_file',
        )

        # Add diverging commits to fork, including some changes similar to upstream
        self._add_commits(
            fork_repo, author='fork-dev', num_commits=3, filename_prefix='fork_diverge'
        )
        self._add_similar_commits(fork_repo, upstream_repo, author='fork-dev')

    def _add_commits(self, repo, author, num_commits, filename_prefix):
        for ind in range(num_commits):
            filename = f'{filename_prefix}_{ind}.txt'
            content = f'Content for {filename}, created by {author}'
            message = f'Commit {ind} by {author}'
            create_file_and_commit(repo, author, filename, content, message)
