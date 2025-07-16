# 自用签到脚本

自用脚本，请勿传播。适用于多种 app 与论坛，解放双手自动化。适配青龙面板。
selenium 自动化 python 脚本必须先安装 chromium 及 chromium-chromedriver。

## CloChat

适用于 CloChat 论坛，包含签到功能。

### 环境变量
- `CLOCHAT_USERNAME`: CloChat 的用户名（必需）
- `CLOCHAT_PASSWORD`: CloChat 的密码（必需）

## Nodeloc

适用于 Nodeloc 论坛，包含签到功能。
～～增加任务脚本，已实现自动点击话题及点赞功能。～～
为了论坛健康发展，已删除部分功能。

### 环境变量
- `NL_COOKIE`: NodeLoc 的 Cookie（必需）

## NodeSeek

适用于 NodeSeek 论坛，包含签到～～、评论和加鸡腿功能。强烈建议修改随机词。否则容易被举报被禁言～～。
为了论坛健康发展，已删除部分功能。

### 功能特点

- 自动签到（点击签到图标）
- 自动点击"试试手气"或"鸡腿 x 5"按钮（可配置）
- ～～随机选择帖子进行评论～～
- ～～自动给帖子加鸡腿（7天内的帖子）～～
- ～～随机评论内容（"bd"、"绑定"、"帮顶"）；ai评论功能慎用，极易被举报！～～
- 支持 GitHub Actions 自动运行
- 支持无头模式（可配置）

### 环境变量配置

- `NS_COOKIE`: NodeSeek 的 Cookie（必需）
- `NS_RANDOM`: 是否随机选择奖励，true/false（可选）
- `HEADLESS`: 是否使用无头模式，true/false（可选，默认 true）
- `randomInputStr`: 评论内容

## sfsy

适用于顺丰app，包含签到、抽奖、蜂蜜任务等功能。

### 环境变量
- `sfsyUrl`: 顺丰app捉包提取请求头中的url
