# Development notes

## TODOs
- add type hints and mypy.
- create a minimal realistic example of a merge conflict that can be applied to any file in any pair of repos.

## Troublesome real-world scenarios
### Updating local branches after force-pushed changes

### Cherry-picking a single commit that involves a merge conflict

### Rebasing a local feature branch on main after a squash merge
The feature branch retains the individual commits that were squashed during the merge, so naive interactive rebasing involves resolving conflicts as each of the squashed commits is replayed on top of main. 

## Conceptual questions
### Remote-tracking branches
How are remote-tracking branches different from 'normal' local branches? Can they be set up manually (e.g. without using `git push --set-upstream` or `git checkout --track origin/$some_branch`)?

### Rebasing nomenclature
How is 'ours' and 'theirs' (or, in vs code, 'current' and 'incoming') defined when rebasing with `--onto`?

### 'Moving' branches
What are all of the different ways to 'move' a branch to a different commit? Is there a manual way to do this by editing some internal git object? After moving a branch, how can orphaned commits be retrieved/viewed?

### Examples illustrating usage and pitfalls of git reset, checkout, switch, and restore
The context is that git reset and git checkout were too overloaded, so git switch and git restore were introduced.
