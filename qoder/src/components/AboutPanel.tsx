import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const REPO = "https://github.com/ssenran-star/odb";

export function AboutPanel() {
  return (
    <Card id="about" className="mb-6">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">项目说明</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
        <p>
          <span className="font-medium text-foreground">简介。</span>
          今天吃什么把「下一餐吃什么」收成一次转动、一次搜索和一次反馈。公开体验就是你现在打开的这个站。
        </p>
        <p>
          <span className="font-medium text-foreground">解决的问题。</span>
          午餐和晚餐反复做选择，口味和吃过的记录散落在聊天里，下次又从头想。这里把候选菜、近期记录和喜欢/不喜欢放在同一页。
        </p>
        <p>
          <span className="font-medium text-foreground">核心功能。</span>
          转盘推荐（避开最近吃过和不喜欢的）、按口味搜索、喜欢/不喜欢反馈、用餐历史。配置 PowerContext 后，偏好和历史写入记忆服务；配置 seekdb 后，搜索走向量检索。未配置或连不上时只做本地演示，不会显示已连接。
        </p>
        <p>
          <span className="font-medium text-foreground">仓库。</span>{" "}
          <a className="underline underline-offset-2" href={REPO} target="_blank" rel="noreferrer">
            {REPO}
          </a>
          （分支 <code>qoder</code>）。同名文件也在仓库 <code>qoder/evidence/</code>。
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          <figure className="space-y-1">
            <img
              src="/screenshots/local-demo.png"
              alt="未配置 PowerContext 和 seekdb 时，页脚显示演示模式"
              className="max-h-80 w-full rounded-md border bg-muted object-contain"
            />
            <figcaption>未配置服务：页脚是演示模式，不会写已连接。</figcaption>
          </figure>
          <figure className="space-y-1">
            <img
              src="/screenshots/local-connected.png"
              alt="PowerContext 状态检查成功后，页脚只显示已连接 PowerContext"
              className="max-h-80 w-full rounded-md border bg-muted object-contain"
            />
            <figcaption>只有 /api/services/status 确认连通后，才显示已连接 PowerContext。seekdb 未配置时不出现在这句话里。</figcaption>
          </figure>
        </div>
      </CardContent>
    </Card>
  );
}
