from loguru import logger
from git import Repo
from git import RemoteProgress


# class MyProgressPrinter(RemoteProgress):
#     def update(self, op_code, cur_count, max_count=None, message=''):
#         print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")

repo = Repo("d:/03 mp products/01 cg Git代码/nacos-snapshot")
origin = repo.remotes.origin
message = "123"

if repo.is_dirty(untracked_files=True):
    repo.git.add(A=True)
    repo.index.commit(message)
    origin.pull()
    info = origin.push()
    if info[0].flags > 1023:
        logger.error(f"Error occurs while pushing to remote, "
                     f"summary: {info[0].summary}, flags: {info[0].flags}, commit messages: {message}")

# for push_info in origin.push(progress=MyProgressPrinter()):
#     print("Updated %s to %s" % (push_info.local_ref, push_info.old_commit))

# diff_obj = repo.index.diff(repo.head.commit)
# print(diff_obj)
# for diff_added in diff_obj.iter_change_type("T"):
#     print(diff_added)
