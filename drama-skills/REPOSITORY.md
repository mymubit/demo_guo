# drama-skills 导出分支

> 本文件只描述镜像推送方式，不是仓库结构说明书；仓库结构与使用方式见 `README.md`。

此分支仅用于镜像到独立仓 `mymubit/demo_guo` 的 `drama-skills` 分支。

```bash
git clone -b drama-skills-export https://github.com/mymubit/demo4book.git /tmp/skills-mirror
cd /tmp/skills-mirror
git push https://github.com/mymubit/demo_guo.git HEAD:drama-skills
```
