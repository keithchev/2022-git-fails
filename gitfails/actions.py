import os
import pathlib
import git


def email_from_author_name(author_name):
    return f"{author_name}@some-domain.com"


def create_repo(repo_dirpath):
    if not os.path.exists(repo_dirpath):
        os.makedirs(repo_dirpath)

    repo = git.Repo.init(repo_dirpath)
    return repo


def create_branch_and_checkout(repo, branch_name):
    if branch_name not in repo.heads:
        repo.create_head(branch_name)
    repo.heads[branch_name].checkout()


def commit_file(repo, author, filename, message):
    repo.index.add([filename])
    author = git.Actor(name=author, email=email_from_author_name(author))
    repo.index.commit(message, author=author)


def commit_files(repo, author, filenames, message):
    repo.index.add(filenames)
    author = git.Actor(name=author, email=email_from_author_name(author))
    repo.index.commit(message, author=author)


def create_file(repo, filename, content):
    """
    Create a new file.
    """
    filepath = pathlib.Path(repo.working_tree_dir, filename)
    if filepath.exists():
        raise ValueError(f"File {filepath} already exists")

    if not content.endswith("\n"):
        content += "\n"

    with open(filepath, "w") as file:
        file.write(content)


def modify_file(repo, filename, content, overwrite=False):
    """
    Modify an existing file (by either appending to or overwriting it).
    """
    filepath = pathlib.Path(repo.working_tree_dir, filename)
    if not filepath.exists():
        raise ValueError(f"File {filepath} does not exist")

    if not content.endswith("\n"):
        content += "\n"

    mode = "w" if overwrite else "a"
    with open(filepath, mode) as file:
        file.write(content)


def create_file_and_commit(repo, author, filename, content, message):
    """
    Create a new file and commit it.
    """
    create_file(repo, filename, content)
    commit_file(repo, author, filename, message)


def modify_file_and_commit(repo, author, filename, content, message, overwrite=False):
    """
    Modify an existing file (by either appending to or overwriting it)
    and commit the change.
    """
    modify_file(repo, filename, content, overwrite=overwrite)
    commit_file(repo, author, filename, message)
