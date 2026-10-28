# 提测粘贴表

登录大赛测试平台，进入 Qoder 赛题提交入口后，按下面填写。UID 不要猜。线上函数在重新发布前仍可能 404，不要把本地结果写成线上已经通过。

## 表单

| 项 | 填写 |
| --- | --- |
| 项目网站网址 | https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone |
| 代码仓库 | https://github.com/ssenran-star/odb |
| Branch | `qoder` |
| Commit | 与 GitHub 上分支 `qoder` 的最新提交一致。用 `git rev-parse HEAD` 复制完整 SHA。不要填旧的 `7ca69f74e38ba9e19b88f2cc3ad86b79834bf890`。 |
| Qoder UID | （空。在 Qoder → 设置 → 个人资料 → 编辑 复制。同一串也写入 `evidence/QODER_UID.txt`。） |

可见范围必须是「任何人都可访问」。企业版账号做不到公开，请用个人账号发布。

## 一并上传或粘贴的材料

- 运行说明：`qoder/RUN.md`
- 验证样例：`qoder/VERIFY.md`
- 指定技术记录：`qoder/evidence/powercontext-remember-search.json`
- 重新发布前的站点抓取：`qoder/evidence/sites-homepage.png`、`sites-homepage.html`、`sites-api-probe.txt`
- 本地界面：`qoder/evidence/local-demo.png`、`qoder/evidence/local-connected.png`
- Qoder 开发对话截图或录屏：仓库里没有。需要参赛者从自己的 Qoder 会话导出后另附。本次云端修改不能代替 Qoder 开发记录。

## 基础验收对照（按推送时的事实，不是按重新发布之后）

1. 网站可访问。**通过（页面）。** 无痕或未登录可以打开上面的 Sites URL，首页 HTTP 200。函数路由当时仍 404，见 `evidence/sites-api-probe.txt`。
2. 项目能够运行。**本地通过，线上函数未通过。** 按 `RUN.md` 可在本机启动，并按 `VERIFY.md` 样例 A、样例 B 跑通。公开站点上的 `/functions/v1/app` 在这次推送前返回 404，评审若只点旧站点，主要功能仍会退回浏览器本地逻辑。重新发布后应再测一次。
3. Qoder 开发可核对。**未通过。** UID 为空，仓库里没有可核对的 Qoder 对话记录。补上 UID 和开发过程截图之前，不要勾此项。
4. 技术结合有效。**代码和本地记录通过，已发布站点未通过。** PowerContext 的 remember / search 已经在功能路径里，证据 JSON 是这次真实调用。seekdb 没有配置，也没有写成已连接。公开站点还没带上新代码和 Secrets，页脚旧文案与 404 矛盾。重新发布且 `powerContext.status` 为 `connected` 之后，此项才对线上成立。

## 发布后建议再做的四步

1. Qoder Desktop 拉取 `qoder`，Sites 重新发布，可见范围「任何人都可访问」。
2. Sites Secrets 写入 `POWERCONTEXT_URL` 和 `POWERCONTEXT_SCOPE_ID`。隧道主机变了就换新的 URL。不要提交 token。
3. 无痕窗口打开站点，确认页脚与 `/functions/v1/app/api/services/status` 一致，把结果填进 `VERIFY.md` 文末空位。
4. 复制 UID，连同仓库、分支、最新 commit、网站 URL 提交到大赛平台。
