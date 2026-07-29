> **状态：历史规划稿。** 当前无 `cns_` 前缀的直接 API、已实现范围和示例以 `r/README_zh.md` 为准；下文 token 对象示例不属于当前公开 API。

# cnsplots 原生 R 版本项目路线图

状态：内部规划已形成，上游 RFC 待确认
工作分支：`feature/r-package-foundation`
Python 参考版本：`0.5.0`
参考提交：`e678e2d5e975c4595b1d7c8bc4d07b4030a29d14`
R 包拟用名称：`cnsplots`
当前阶段：只完成规划文档，尚未创建 `r/` 包、安装 R 依赖或修改 CI

## 1. 对原项目的判断

当前仓库是一个以 Python 为主体的科学绘图包，核心建立在 Matplotlib、
Seaborn、Scanpy 及若干专业绘图和统计后端之上。

作者公开了 31 个绘图入口，并提供：

- 全局 `settings`；
- Matplotlib 和 Scanpy 样式设置；
- palettes、Figure、save、multipanel；
- 生存、GSEA、热图、集合图、Sankey 等专业功能；
- Cox、L1 logistic regression 和 prerank 等分析封装。

现有 R 支持只有 Python 函数 `setup_ggplot()`。该函数根据四个 Python
settings 返回一段 R 代码字符串，定义一个简单的 `theme()`。它没有：

- 可安装的 R 包；
- 原生 R API；
- palettes 对应的 ggplot2 scales；
- 针对不同 Figure 类型的主题；
- 物理尺寸与出版导出层；
- R 测试和 R 文档。

因此，这项工作不是“补几个 R 函数”，而是建立第一个真正原生的 R
实现。

## 2. 产品目标

R 版首先解决两个明确问题：

1. 每张 ggplot 都要重复编写大量 `theme()` 代码；
2. 一个固定预设不能同时满足分布图、UMAP、矩阵图和组合图。

目标不是创造一个更大的“万能 theme”，而是把稳定规范和 Figure
差异拆开：

```text
设计 tokens
    ↓
完整基础主题
    ↓
一个语义 profile
    ↓
零到两个局部 component
    ↓
用户最后的 theme() 覆盖
```

字体、字号、线宽和颜色等稳定值只定义一次；不同 Figure 只选择对应
profile；少数例外使用 component；最终仍保留完整 ggplot2 自由度。

## 3. 五个核心概念

| 概念 | 负责什么 | 不负责什么 |
|---|---|---|
| token | 字体、字号、线宽、间距、前景和背景色 | 图形几何、统计检验 |
| profile | 一类 Figure 的非数据视觉起点 | 坐标系统、facet 构造、数据转换 |
| component | legend、axis、facet、grid、spacing 的局部修改 | 重置完整主题 |
| recipe | 后续某类图的几何和数据整理 | 偷偷执行推断统计 |
| figure spec | 物理宽高、单位、DPI、背景和设备约束 | Matplotlib Figure/Axes 仿真 |

硬性规则：

> `settings()` 是设计值的唯一真源；`setup_ggplot()` 返回完整主题；
> profile 在内部组合；公开 component 是不完整的增量 patch；用户最后
> 添加的 `theme()` 永远优先。包加载和函数构造均不修改全局 theme、
> options、字体或设备。

## 4. 仓库组织

采用当前 monorepo 下的自包含 `r/` 子包：

```text
cnsplots/
├── src/cnsplots/          # 原有 Python 包
├── tests/                 # 原有 Python 测试
├── docs/                  # 双语言规划和功能映射
├── pyproject.toml
└── r/                     # 原生 R 包根目录
    ├── DESCRIPTION
    ├── NAMESPACE
    ├── LICENSE
    ├── README.Rmd
    ├── README.md
    ├── NEWS.md
    ├── R/
    ├── tests/testthat/
    ├── vignettes/
    └── man/
```

选择该结构的原因：

- 原作者可以在一个 PR 中审阅 Python/R 的关系；
- Python 根目录和构建流程不被改造成双重包根目录；
- `r/` 可单独执行 `R CMD build` 和 `R CMD check`；
- 可使用 `remotes::install_github(..., subdir = "r")` 安装；
- 如果未来维护和发布完全独立，仍可保留历史地拆成单独仓库。

`r/` 必须自包含，构建时不能读取 `../src` 或 `../LICENSE.md`。

## 5. 首期公共 API

### 5.1 Tokens 与主题

```r
tokens <- settings(
  base_family = "Arial",
  base_size = 8
)

p +
  setup_ggplot(profile = "embedding", tokens = tokens) +
  theme_legend(position = "bottom") +
  theme(plot.margin = margin(2, 2, 2, 2, unit = "mm"))
```

拟冻结的主题 API：

```r
settings(...)
settings_update(tokens, ...)

setup_ggplot(profile = "standard", tokens = settings())

theme_axes(...)
theme_legend(...)
theme_facet(...)
theme_grid(...)
theme_spacing(...)
```

`setup_ggplot()` 不同时接受独立的 `base_size` 和 `base_family`，避免与
tokens 出现两个配置真源。

### 5.2 Profiles

PR 1 用两个 profile 证明分派机制：

- `standard`：完整左/下轴、无网格、常规 legend；
- `embedding`：适合 UMAP、t-SNE、空间图的无轴或弱轴布局。

完整 0.1.0 再增加：

- `distribution`：适合 box、violin、bar 等类别/数值轴；
- `matrix`：适合 tile、表达矩阵等密集行列标签。

`compact` 和 `multipanel` 是正交的布局/间距问题，不作为互斥
profile。`polar` 和 `survival` 等到对应 recipe 出现后再确定契约。

### 5.3 Palettes 与 scales

```r
palette_names(kind = "all")
palettes(color, n = NULL, direction = 1)

scale_colour_palette(...)
scale_fill_palette(...)
scale_colour_map(...)
scale_fill_map(...)
```

规则：

- 对照 Python 0.5.0 的具体 commit 保存名称、hex 和顺序；
- qualitative、sequential、diverging 必须有类型元数据；
- 离散颜色数量不足时明确报错，不静默循环或伪造新类别颜色；
- Cell、Nature、Science 只能称为“期刊启发式 palette”；
- 未验证前不宣称色盲安全或符合某期刊正式规范；
- 11 个 Python 单色常量不机械复制成 11 个 R 全局对象。

### 5.4 Figure spec 与导出

```r
spec <- figure(
  width = 89,
  height = 70,
  units = "mm",
  dpi = 300,
  background = "white"
)

savefig(
  filename = "figure-1.tiff",
  plot = p,
  spec = spec
)
```

规则：

- 物理尺寸使用 mm、in 或 pt；
- DPI 只决定 raster 像素，不改变 PDF/SVG 物理尺寸；
- 扩展名和显式 device 冲突时错误退出；
- 默认背景白色，透明必须显式请求；
- Python 的线宽数字不能直接复制到 ggplot2，必须做 pt/mm 语义转换；
- 不预设所谓通用单栏/双栏宽度，除非核对目标期刊的一手指南。

## 6. 分阶段实施

### M0：规划与上游确认

产物：

- 英文架构规划；
- Python→R 功能矩阵；
- 中文路线图；
- 可直接发布的上游 RFC 草案。

上游需确认：

- 是否接受 monorepo 中的 `r/`；
- 包名和独立版本；
- `Authors@R` 与 maintainer；
- GitHub-only 还是未来 CRAN；
- 首个 PR 是否允许独立 R CI；
- 首个 PR 的最小范围。

### M1 / PR 1：主题架构证明

只提交一个可安装、可测试的小切片：

- 自包含 R package metadata 和许可证；
- `settings()`；
- `setup_ggplot()`；
- `standard`、`embedding`；
- `theme_legend()`；
- 一套代表性离散 palette；
- colour/fill 离散 scales；
- testthat 和最短 README。

至少两个 profile 才能证明 profile 机制；至少一个 component 才能证明
“后添加者覆盖前者”。本 PR 不代表完整 0.1.0 已完成。

### M2 / PR 2：完整 theme kernel

- `distribution`、`matrix`；
- axis、legend、facet、grid、spacing components；
- token 验证和物理单位转换；
- 组合优先级与无副作用测试；
- 少量固定环境视觉回归。

### M3 / PR 3：完整 palettes 与 scales

- 完成来源审计；
- 迁移保留的离散、连续和发散 palettes；
- exact-value fixtures；
- 离散/连续 colour/fill scales；
- 如来源或 diff 太大，拆成 PR 3a/3b。

### M4 / PR 4：出版尺寸与导出

- `figure()`；
- `savefig()`；
- PDF、SVG、PNG、TIFF；
- vector/raster 设备策略；
- 物理宽高与 raster 像素的实测；
- 字体、Illustrator 和 rasterization 说明。

### M5：0.1.0 文档和发布就绪

- README、函数文档、vignettes；
- Python/R 差异说明；
- 完整 `R CMD check`；
- 现有 `make test` 和 `make lint`；
- 上游同意后决定 GitHub release 或 CRAN。

### M6：绘图 recipes

按真实发文需求分批增加，不一次复制 31 个 Python 函数：

1. distribution；
2. categorical/composition；
3. relationships；
4. volcano、dot 等通用生信图；
5. diagnostics 和 forest；
6. heatmap、survival、set、flow、phylo 等专业后端。

统一使用 `cns_plot_box()`、`cns_plot_volcano()` 等前缀，避免遮蔽
`graphics::hist()`、`stats::dist()` 等常用函数。

## 7. 31 个 Python 绘图功能的处理原则

31 个入口已经全部进入功能矩阵，没有遗漏。

首期主题包不承诺完整绘图对等。迁移分为：

- P1 通用 ggplot recipe：box、violin、scatter、line、volcano 等；
- P1/P2 双层：通用 tidy 输入先实现，对模型对象或单细胞对象的 adapter
  后实现，例如 dot、forest、ROC；
- P2 专业后端：heatmap、survival、cumulative incidence、phylo、
  upset、venn、sankey；
- Defer 分析框架：CoxModel、LogisticModel、prerank。

热图等非 ggplot 对象可以共享 tokens、palette 和字体规范，但不能承诺
`setup_ggplot()` 直接作用于 ComplexHeatmap。

## 8. 统计与绘图必须解耦

```text
compute_*()   统计计算
tidy_*()      标准化结果
cns_plot_*()  几何和数据展示
annotate_*()  可选统计标注
setup_ggplot*()  非数据外观
```

例如：

- box/violin 不因几何类型自动运行 Wilcoxon；
- bar/lollipop 不自动运行 Welch t-test；
- stack 不自动运行 Fisher/chi-square；
- reg 的 Pearson 结果是显式 annotation；
- ROC 曲线显示与 AUC/CI 估计分开；
- volcano 阈值和标签选择必须是可见参数。

这样更符合 R 生态，也避免实验设计一变化就需要修改绘图函数。

## 9. 版本、许可证和发布

版本顺序：

```text
初始开发       0.0.0.9000
首次发布       0.1.0
发布后开发     0.1.0.9000
首个 R tag     r-v0.1.0
```

不能从 `0.1.0.9000` 再发布为 `0.1.0`，因为那会造成版本下降。

Python 继续保持 0.5.x 和 `v*` tag；`r-v*` 不会触发当前以 `v*`
匹配的 PyPI workflow。

许可证继续使用 BSD-3-Clause：

- 根 `LICENSE.md` 不修改；
- `r/DESCRIPTION` 使用 `BSD_3_clause + file LICENSE`；
- `r/LICENSE` 自包含，不能引用父目录或使用符号链接；
- Farid Rashidi 的原始版权和设计贡献需要保留；
- R 实现贡献者和 `cre` 必须经本人和上游确认；
- 第三方 palette 需要追溯最初来源，而不只注明 Python 文件。

## 10. 默认值和依赖边界

内部拟定默认值：

| 项目 | 默认 |
|---|---|
| R | >= 4.1.0 |
| ggplot2 | >= 3.4.0 |
| base family | `sans` |
| base size | 8 pt |
| secondary size | 7 pt |
| foreground | black |
| theme/export background | white |
| raster DPI | 300 |
| transparent background | 显式请求 |
| layout backend | phase one 不冻结 |

`ggplot2 >= 3.4.0` 是因为使用 `linewidth`，但最低版本最终必须通过
CI 实测，而不是只写入 DESCRIPTION。

预期运行依赖尽量只有：

- ggplot2；
- 直接使用时的 grid 和 grDevices；
- 只有源码直接调用时才加入 scales。

testthat、vdiffr、ragg、svglite、knitr、rmarkdown 均按实际功能加入
Suggests。首期不提交 `renv.lock`，不提前引入 Seurat、
ComplexHeatmap、survival 或整个 tidyverse。

## 11. 验收证据

PR 1 只有同时满足以下条件才算架构证明成功：

1. `r/` 能独立安装、build 和 check；
2. `setup_ggplot()` 返回完整 theme，且不改变全局状态；
3. standard 与 embedding 的契约有语义测试；
4. component 和最终用户 `theme()` 的覆盖顺序有测试；
5. palette hex 顺序及 colour/fill scale 有测试；
6. README 示例实际可运行；
7. 原 Python 测试和 lint 仍通过。

完整 0.1.0 还必须证明：

- 四个首期 profiles 和全部 components；
- 保留 palettes 的来源与 exact-value parity；
- vector/raster 物理尺寸；
- 至少五类代表性 Figure；
- 无未验证的期刊合规声明；
- R CMD check 无 error/warning；
- 每个 PR 都是独立、可审阅的增量。

## 12. 当前环境与实施门禁

已核实：

- WSL 当前没有 `R` 或 `Rscript` 在 PATH；
- Windows 已安装 R 4.5.3；
- 当前 Windows R 中还没有 ggplot2、testthat 和 devtools；
- 从 WSL UNC 工作目录调用 Windows R 会出现 CMD 工作目录警告。

因此规划完成后，正式实现前要先选择可复现开发方式。依赖安装、CI、
根 Makefile 和 release workflow 均不会在没有明确批准时修改。

## 13. 当前已冻结与仍待确认

内部已冻结：

- 当前仓库中的自包含 `r/`；
- R-native 而非逐行翻译；
- tokens → profile → component → user override；
- `cnsplots` 作为拟用包名；
- `savefig()`；
- 初始版本和最低版本建议；
- 首期 profiles/components；
- statistics/plot/theme/export 分层；
- 小 PR 顺序。

仍需上游作者确认：

- 是否接受该目录和产品边界；
- Authors@R、版权角色和 R maintainer；
- 是否考虑 CRAN；
- 是否允许独立 path-filtered R CI；
- palette 来源和必保留优先级；
- 是否接受第一个架构证明 PR。

在上游 RFC 得到回应前，不开始大规模移植，也不把 31 个绘图函数一次
塞进首个 PR。
