# cnsplots R 完整使用指南

这是 Python **cnsplots 0.5.0** 的原生 R/ggplot2 实现。它保留作者的
palette、主要视觉规则、默认统计语义和直接函数名，但所有绘图函数都返回
普通的 `ggplot` 对象：可以继续使用 `+ theme()`、`+ labs()`、替换 scale，
也可以交给任何支持 ggplot2 的组合工具。

R 版不追求 Matplotlib 与 ggplot2 的逐像素一致，也不会在加载包时调用
`theme_set()`、打开图形设备或修改用户数据。

> 当前 R 包版本：`0.0.0.9000`
> 对照 Python 版本：`0.5.0`
> 对照提交：`e678e2d5e975c4595b1d7c8bc4d07b4030a29d14`

## 目录

1. [安装](#1-安装)
2. [三分钟上手](#2-三分钟上手)
3. [数据和返回值约定](#3-数据和返回值约定)
4. [theme：少写代码但保留单图控制](#4-theme少写代码但保留单图控制)
5. [settings：统一修改稳定默认值](#5-settings统一修改稳定默认值)
6. [palettes 和 scales](#6-palettes-和-scales)
7. [物理尺寸和导出](#7-物理尺寸和导出)
8. [18 个绘图函数](#8-18-个绘图函数)
9. [推荐的发文作图工作流](#9-推荐的发文作图工作流)
10. [明确的兼容边界](#10-明确的兼容边界)
11. [开发与验证](#11-开发与验证)

## 1. 安装

### 1.1 从当前仓库安装

在仓库根目录运行：

```sh
R CMD INSTALL r
```

### 1.2 从 GitHub 开发分支安装

当前 R 版位于 `jarxunlai/cnsplots` 的 `feature/r-package-foundation`
分支：

```r
install.packages("remotes")
remotes::install_github(
  "jarxunlai/cnsplots",
  ref = "feature/r-package-foundation",
  subdir = "r"
)
```

`remotes` 只是安装工具，不是 cnsplots 的运行依赖。如果 R 版以后合并到
原作者的 `main`，可以改为：

```r
remotes::install_github("faridrashidi/cnsplots", subdir = "r")
```

### 1.3 加载与确认

```r
library(ggplot2)
library(cnsplots)

packageVersion("cnsplots")
palette_names()
```

`boxplot()`、`barplot()`、`qqplot()` 等名称可能和 base R 或其他包冲突。
有冲突时直接使用 `cnsplots::boxplot()` 这类 namespaced call，不需要给所有
函数再加一层 `cns_` 前缀。

## 2. 三分钟上手

绘图函数中的列参数使用字符串，与作者的 Python API 保持一致：

```r
p <- scatterplot(
  iris,
  x = "Sepal.Length",
  y = "Petal.Length",
  hue = "Species"
)

p + labs(
  title = "Iris morphology",
  x = "Sepal length",
  y = "Petal length"
)
```

构造器已经应用默认 palette 和主题。单张图有特殊要求时，继续叠加即可：

```r
p_publication <- p +
  labs(title = "Iris morphology") +
  theme_legend(position = "bottom", direction = "horizontal") +
  theme_grid(major = "y") +
  theme(plot.title = element_text(hjust = 0))
```

按最终物理尺寸保存：

```r
savefig(
  "figures/iris.pdf",
  p_publication,
  width = 85,
  height = 65,
  units = "mm",
  background = "white"
)
```

## 3. 数据和返回值约定

### 3.1 直接、可检查的数据接口

- `data` 必须是非空 `data.frame`；
- `x`、`y`、`hue`、`stack` 等列名使用长度为 1 的字符串；
- 数值轴要求有限数值；分类顺序使用 `order`、`hue_order` 或
  `stack_order` 显式给出；
- 完整顺序参数不能偷偷过滤观测到的 level；
- 输入数据不会被原地修改；
- 不支持的参数会明确报错，而不是静默忽略。

### 3.2 返回普通 ggplot

```r
p <- boxplot(iris, "Species", "Sepal.Length")

inherits(p, "ggplot")
p +
  scale_y_continuous(limits = c(4, 8.5)) +
  labs(tag = "A") +
  theme(plot.tag = element_text(face = "bold"))
```

构造函数不会自动打印或保存。交互式会话中把 `p` 放在一行即可显示；脚本中
可以显式 `print(p)`。

## 4. theme：少写代码但保留单图控制

### 4.1 基础主题

`setup_ggplot()` 依据作者正式的 `setup_matplotlib()` 和 `setup_ax()`
实现基础风格：标题和轴标题 8 pt、tick 和 legend 7 pt、只保留左/下轴、
默认无网格、透明画布，并使用出版尺度的线宽。

```r
ggplot(iris, aes(Sepal.Length, Petal.Length, colour = Species)) +
  geom_point() +
  scale_colour_palette("Ecotyper1") +
  setup_ggplot()
```

三个 profile 只负责非数据视觉：

| profile | 用途 | 轴的行为 |
| --- | --- | --- |
| `standard` | 散点、回归、分布、类别图 | 保留左/下轴和标签 |
| `embedding` | UMAP、t-SNE、空间坐标 | 隐藏轴线、tick、标签和标题 |
| `matrix` | confusion matrix、tile、表达矩阵 | 保留行列文字，隐藏轴线和 tick |

```r
p + setup_ggplot("standard")
p + setup_ggplot("embedding")
p + setup_ggplot("matrix")
```

可为一张图直接覆盖字体，不需要修改全局 theme：

```r
p + setup_ggplot(base_family = "sans", base_size = 9)
```

字体是否真正可用由操作系统和图形设备决定。默认的 `"sans"` 最便携；只有在
确认导出 device 已注册 Arial 后，再把 `base_family` 改为 `"Arial"`。

### 4.2 小型 theme components

component 是不完整的增量 theme，不会重置已经存在的完整 theme：

```r
p +
  theme_axes(x = TRUE, y = TRUE, ticks = FALSE) +
  theme_legend(position = "bottom", direction = "horizontal", title = FALSE) +
  theme_facet(background = FALSE, face = "bold", size = 7) +
  theme_grid(major = "y", minor = "none", colour = "grey90") +
  theme_spacing(
    plot_margin = c(4, 4, 4, 4),
    panel_spacing = 3,
    legend_spacing = 2
  )
```

| 函数 | 主要任务 |
| --- | --- |
| `theme_axes()` | 分别控制 x/y 轴、tick、tick label 和轴标题 |
| `theme_legend()` | legend 位置、方向和标题 |
| `theme_facet()` | facet strip 背景、字体和字号 |
| `theme_grid()` | major/minor grid 在 x/y/both/none 中选择 |
| `theme_spacing()` | plot margin、panel spacing 和 legend spacing，单位为 pt |

叠加顺序遵循 ggplot2 规则：**后添加者优先**。因此最后的
`ggplot2::theme()` 永远可以精确覆盖包内默认值：

```r
p +
  theme_legend(position = "bottom") +
  theme(legend.position = "left")
```

包不会调用 `theme_set()`。如果用户自己选择全局设置，那是普通 ggplot2
行为，不是 cnsplots 的隐式副作用。

## 5. settings：统一修改稳定默认值

### 5.1 查看

```r
all_settings <- settings()
length(all_settings)                    # 78
settings("title_fontsize")              # 单个值
settings("palette_qual", "savefig_dpi") # 多个值
```

最常用的设置包括：

| key | 默认值 | 作用 |
| --- | ---: | --- |
| `palette_qual` | `Ecotyper1` | 默认离散 palette |
| `palette_seq` | `gnuplot` | 默认连续 colour map |
| `title_fontsize` | `8` | 标题和轴标题字号 |
| `legend_fontsize` | `7` | legend 和常规辅助文字字号 |
| `axes_linewidth` | `0.5` | 轴线宽度，pt |
| `axes_grid` | `FALSE` | 基础主题是否显示 major grid |
| `annotation_auto_contrast` | `TRUE` | 深色背景上的文字自动切换为白色 |
| `savefig_dpi` | `288` | 默认 raster DPI |
| `savefig_transparent` | `TRUE` | 默认透明导出 |
| `figure_width` / `figure_height` | `150` | 默认 150 pt，即 150/72 inch |

`settings()` 保留了 Python 的 78 个键以便对照，但不是每个 Matplotlib、
Scanpy 或 multipanel 设置都能直接影响 ggplot2。当前会实际影响主题、palette、
figure 或 export 的设置应以函数文档和测试为准。

### 5.2 更新、临时更新和恢复

```r
# 更新当前 R 会话中后续创建的图
old <- settings(
  title_fontsize = 9,
  legend_fontsize = 8,
  palette_qual = "Nature"
)

# 只在一个表达式中生效；即使表达式报错也会恢复
p_large <- with_settings(
  list(title_fontsize = 10, legend_fontsize = 9),
  scatterplot(iris, "Sepal.Length", "Petal.Length", hue = "Species")
)

# 恢复全部作者默认值
reset_settings()
```

设置只影响**之后构造**的主题、scale、figure 或图，不会回头修改已经创建的
ggplot 对象。它们只保存在当前 R 进程中，不写入用户配置文件。

## 6. palettes 和 scales

### 6.1 查看 palette

```r
palette_names()
palette_names("qualitative")
palette_names("continuous")
palette_names(details = TRUE)
```

当前锁定 Python 0.5.0 的 28 个 qualitative palettes：

```text
Set1, Set2, Set3, Pastel1, Pastel2, Paired, Dark2, Accent,
Tableau, Bold, BlueRed, Cell, Nature, Science, Lancet, NEJM,
JAMA, JCO, OkabeIto, TolBright, TolMuted, ECharts,
Ecotyper1, Ecotyper2, Ecotyper3, Ecotyper4, Ecotyper5, Ecotyper6
```

以及 7 个 continuous maps：

```text
BuRd_custom, WhYlOrRd_custom, OrBu_custom, YlGnBu_custom,
parula, gnuplot, hot
```

`Cell`、`Nature`、`Science` 等名称表示作者采用的期刊启发式颜色集合，
不应解释为期刊官方规范或普遍色盲安全认证。

### 6.2 取得颜色

```r
palettes("Ecotyper1")
palettes("Ecotyper1", n = 4)
palettes("Ecotyper1", n = 4, direction = -1)
palettes(c("#D6372E", "navy", "grey80"))

# R 使用从 1 开始的索引
get_hexcolors_from_apalette(c(1, 3, 5), "Set1")
```

qualitative palette 在 `n` 超过原生长度时按作者顺序循环，匹配
Matplotlib property cycle；continuous map 返回固定的 256 色 lookup table。

11 个常用单色常量也可直接使用：

```r
RED; BLUE; GREEN; PURPLE; ORANGE; YELLOW
BROWN; PINK; GRAY; VIOLET; CHOCOLATE
```

### 6.3 ggplot2 scales

```r
# 离散 colour/fill
p + scale_colour_palette("Nature")
cnsplots::boxplot(iris, "Species", "Sepal.Length") +
  scale_fill_palette("Set2", drop = FALSE)

# color 拼写别名也可用
p + scale_color_palette("Nature")

# 连续 colour/fill
ggplot(mtcars, aes(wt, mpg, colour = hp)) +
  geom_point(size = 2) +
  scale_colour_map("gnuplot") +
  setup_ggplot()

ggplot(mtcars, aes(factor(cyl), factor(gear), fill = mpg)) +
  geom_tile() +
  scale_fill_map("BuRd_custom") +
  setup_ggplot("matrix")
```

给构造器传 `palette = c("#...", "#...")` 可以使用自定义离散颜色；
连续 map 可以使用包内名称、受支持的常见 Matplotlib 名称、`_r` 反向名称，
或颜色向量。Matplotlib colormap 对象本身不能传入 R。

## 7. 物理尺寸和导出

### 7.1 figure specification

```r
spec <- figure(
  width = 85,
  height = 65,
  units = "mm",
  dpi = 300,
  background = "white"
)

spec
spec$width_mm
spec$pixel_width
```

支持 `pt`、`mm`、`cm`、`in` 和兼容旧 Python 命名的 `px72`。`px72` 与
`pt` 都表示 1/72 inch，不是最终 raster pixel。

默认 `figure()` 是 150 × 150 pt，按默认 288 DPI 导出时为 600 × 600 px。
PDF/SVG/EPS 的物理尺寸由 width/height 决定；DPI 只决定 PNG/TIFF/JPEG 等
raster 输出的像素数。

`figure()` 中的 `palette` 和 `cmap` 用于记录作者的 figure 配置和复现信息，
不会追溯性改变已经建好的 ggplot。实际颜色仍由绘图函数或 scale 决定。

### 7.2 保存

```r
# 直接传物理尺寸
savefig(
  "figures/panel-a.pdf",
  p,
  width = 85,
  height = 65,
  units = "mm",
  background = "white"
)

# 多张图复用一个 spec
spec <- figure(85, 65, units = "mm", dpi = 600, background = "white")
savefig("figures/panel-a.png", p, spec = spec)
savefig("figures/panel-a.tiff", p, spec = spec, compression = "lzw")
```

支持：PDF、SVG、PNG、TIFF/TIF、JPEG/JPG 和 EPS。父目录会自动创建，
返回值是不可见的规范化文件路径。

扩展名决定 device；显式 `device` 与扩展名冲突会报错。使用 `spec` 时不要
同时传 `width`/`height`。发文图通常建议显式指定 `background = "white"`，
避免默认透明背景在投稿系统中出现意外显示。

## 8. 18 个绘图函数

下面的示例只依赖 base R、ggplot2 和 cnsplots。

### 8.1 示例数据

```r
set.seed(42)

demo <- data.frame(
  group = rep(c("Control", "Treatment"), each = 30),
  subtype = rep(c("A", "B", "C"), length.out = 60),
  value = c(rnorm(30, 5, 0.8), rnorm(30, 6, 1.0)),
  score = seq_len(60) + rnorm(60, sd = 5)
)
```

### 8.2 关系图

#### `scatterplot()`

```r
p_scatter <- scatterplot(
  demo, "score", "value",
  hue = "group",
  hue_order = c("Control", "Treatment"),
  palette = "Ecotyper1",
  alpha = 0.8
)
```

`s` 使用作者的 Matplotlib marker area 语义，额外参数传给
`geom_point()`。

#### `regplot()`

```r
p_reg <- regplot(demo, "score", "value")
p_reg_grouped <- regplot(
  demo, "score", "value",
  hue = "group",
  hue_order = c("Control", "Treatment"),
  level = 0.95
)
```

未分组时绘制整体线性拟合、置信带和 Pearson `r/P`；设置 `hue` 时每组分别
拟合并标注。`color` 既可以是一个 R 颜色，也可以是数据列名。

#### `slopeplot()`

```r
paired <- expand.grid(
  cohort = c("Cohort 1", "Cohort 2"),
  subject = seq_len(6),
  condition = c("Before", "After"),
  KEEP.OUT.ATTRS = FALSE,
  stringsAsFactors = FALSE
)
paired$pair_id <- interaction(paired$cohort, paired$subject, drop = TRUE)
paired$value <- as.numeric(paired$pair_id) +
  ifelse(paired$condition == "After", 0.8, 0) +
  rnorm(nrow(paired), sd = 0.15)

p_slope <- slopeplot(
  paired,
  x = "cohort",
  y = "value",
  hue = "condition",
  pair = "pair_id",
  hue_order = c("Before", "After")
)
```

`hue` 必须恰好有两个条件；每个 pair 必须在同一个 x 组内且每个条件正好一条
记录。

### 8.3 分类汇总和组成图

#### `barplot()`

```r
p_bar <- barplot(
  demo, "group", "value",
  hue = "subtype",
  order = c("Control", "Treatment"),
  hue_order = c("A", "B", "C"),
  add_tip = TRUE
)
```

显示组均值；R 版不会在绘图时隐式添加不确定区间或统计检验。

#### `lollipopplot()`

```r
p_lollipop <- lollipopplot(
  demo, "group", "value",
  hue = "subtype",
  estimator = "mean",
  errorbar = "ci",
  add_tip = TRUE,
  baseline = 0
)
```

`estimator` 支持 `mean`/`median`；`errorbar` 支持 `NULL`、`se`、`sd`、
`ci`。当 x 为数值、y 为分类时会自动绘制横向 lollipop。median 的 SE/CI
使用固定 1,000 次 bootstrap，并恢复调用者 RNG 状态。

#### `stackplot()`

```r
p_stack <- stackplot(
  demo,
  x = "group",
  stack = "subtype",
  order = c("Control", "Treatment"),
  stack_order = c("A", "B", "C"),
  normalize = TRUE,
  add_count = TRUE
)

# 横向版本：只提供 y，不提供 x
p_stack_horizontal <- stackplot(demo, y = "group", stack = "subtype")
```

`x` 和 `y` 必须且只能提供一个。默认每根 bar 归一化为比例；
`normalize = FALSE` 绘制计数。`stack_order` 必须完整覆盖观测到的 level，
不会静默丢数据。

#### `stripplot()`

```r
p_strip <- stripplot(
  demo, "group", "value",
  hue = "subtype",
  showmedian = TRUE,
  showmeans = TRUE,
  add_count = TRUE
)
```

median 和 mean 按 x 类别汇总，而不是分别按 hue 汇总，这与作者原函数一致。

### 8.4 分布图

#### `boxplot()`

```r
p_box <- cnsplots::boxplot(
  demo, "group", "value",
  hue = "subtype",
  showoutliers = FALSE,
  add_count = TRUE,
  whis = 1.5
)
```

`whis = c(0, 100)` 可让 whisker 覆盖观测最小值和最大值。额外参数传给
`geom_boxplot()`。

#### `violinplot()`

```r
p_violin <- violinplot(
  demo, "group", "value",
  hue = "subtype",
  add_box = TRUE,
  add_count = TRUE
)
```

默认叠加窄白色 box；`add_box = FALSE` 可关闭。

#### `distplot()`

```r
p_dist <- distplot(demo, "value", bins = 20)
p_dist_grouped <- distplot(
  demo, "value",
  hue = "group",
  hue_order = c("Control", "Treatment"),
  binwidth = 0.4,
  alpha = 0.35
)
```

histogram 与 KDE 共用 bin；KDE 被缩放到 count 轴，可直接和柱高比较。
`binwidth` 优先于 `bins`。

#### `kdeplot()`

```r
p_kde <- kdeplot(demo, "value", add_mode = TRUE, fill = TRUE)
p_kde_grouped <- kdeplot(
  demo, "value",
  hue = "group",
  hue_order = c("Control", "Treatment"),
  adjust = 1
)
```

未分组时 `add_mode = TRUE` 标出估计密度峰。恰好两个 hue group 时会执行并
标注作者原有的 Kolmogorov-Smirnov 检验，同时在 console 输出方法说明。

#### `qqplot()`

```r
p_qq <- cnsplots::qqplot(demo, "value", alpha = 0.8)
```

使用 statsmodels 默认的 `i / (n + 1)` plotting positions；默认不添加
reference line。

### 8.5 圆图和占位图

```r
p_pie <- pieplot(
  demo, "subtype",
  order = c("A", "B", "C"),
  legend = "right"
)

p_donut <- donutplot(demo, "subtype", legend = "bottom")

p_placeholder <- placeholderplot("Panel reserved for validation cohort")
```

`pieplot()` 显示百分比并自动选择黑/白对比文字；`donutplot()` 在中心显示列名，
不显示百分比；`placeholderplot()` 用于先规划 figure panel。

### 8.6 矩阵和组学图

#### `confusionplot()`

```r
classification <- data.frame(
  prediction = c("neg", "neg", "neg", "pos", "pos", "pos", "pos", "neg"),
  truth = c("neg", "neg", "pos", "pos", "pos", "neg", "pos", "neg")
)

p_confusion <- confusionplot(
  classification,
  x = "prediction",
  y = "truth",
  x_order = c("neg", "pos"),
  y_order = c("neg", "pos"),
  add_pvalue = TRUE,
  positive_x = "pos",
  positive_y = "pos"
)
```

`add_pvalue = TRUE` 只支持 2×2 matrix，并增加 specificity、sensitivity、
PPV、NPV、Cohen's kappa、Fisher exact test 和 odds ratio。`x_order`/
`y_order` 必须完整包含全部观测标签。

#### `volcanoplot()`

```r
de <- data.frame(
  log2FoldChange = c(-2.2, -1.1, -0.3, 0.1, 0.7, 1.4, 2.3, 0.2),
  `-log10(adjp)` = c(5, 3, 0.7, 0.2, 2, 3.5, 6, 1.5),
  symbol = paste0("GENE", seq_len(8)),
  check.names = FALSE
)

p_volcano <- volcanoplot(de, n_show = 2)
p_selected <- volcanoplot(de, show_list = c("GENE1", "GENE7"))
```

阈值忠于作者：adjusted p `< 0.05` 且 `abs(log2FC) > 0.5`。自动标签在上、
下调方向分别按 `y * abs(x)` 排名。R 版采用确定性标签偏移，不复刻 Python
`adjustText` 的力导布局。

#### `gseaplot()`

```r
gsea <- data.frame(
  Term = c("Interferon", "Cell cycle", "Oxidative phosphorylation", "ECM"),
  NES = c(2.1, -1.8, 1.5, -1.3),
  `FDR q-val` = c(0.01, 0.02, 0.03, 0.2),
  Overlap = c("12/100", "18/140", "8/80", "5/90"),
  check.names = FALSE
)

p_gsea <- gseaplot(
  gsea,
  y = "Term",
  color = "NES",
  cutoff = 0.05,
  cmap = "BuRd_custom",
  top_term = 20
)
```

先按 `significance_column <= cutoff` 过滤，再按 colour variable 选择 top
terms，最终按 NES 排序。`Overlap` 或 `Tag %` 的 `hits/total` 控制点大小；
两列不能同时提供。函数只画 tidy GSEA 结果，不在内部运行 enrichment 分析。

## 9. 推荐的发文作图工作流

### 9.1 把稳定规范和单图例外分开

```r
base_theme <- setup_ggplot(base_family = "sans", base_size = 8)

p <- scatterplot(iris, "Sepal.Length", "Petal.Length", hue = "Species") +
  base_theme +
  labs(title = "Morphology", x = "Sepal length", y = "Petal length")

# device 已正确注册字体时，可把 sans 换为 Arial
# 只有这张图需要底部 legend 和左对齐标题
p <- p +
  theme_legend(position = "bottom", direction = "horizontal") +
  theme(plot.title = element_text(hjust = 0))
```

### 9.2 先按最终尺寸检查，再导出

```r
single_column <- figure(85, 65, units = "mm", dpi = 600, background = "white")

savefig("figures/figure-1a.pdf", p, spec = single_column)
savefig("figures/figure-1a.png", p, spec = single_column)
```

不要把所谓“通用单栏/双栏宽度”当成期刊事实；最终 width/height 应以目标
期刊当前的一手 author guideline 为准。

### 9.3 保存构图对象而不是依赖最后一张图

虽然 `savefig()` 默认可以使用 `last_plot()`，正式分析脚本更建议显式保存并
传入对象：

```r
p_main <- volcanoplot(de, n_show = 5)
savefig("figures/volcano.pdf", plot = p_main, width = 85, height = 75, units = "mm")
```

这能降低线性分析脚本中“保存错图”的风险。

## 10. 明确的兼容边界

### 10.1 当前会明确报错的功能

- `boxplot()`、`violinplot()`、`lollipopplot()`、`stackplot()` 的
  `pairs` 尚未实现；
- `barplot()` 尚未提供 Python 的 `pairs` 参数；
- Python `barplot(palette = "数据列")` 的歧义重载未保留；
- 任意 Matplotlib colormap 对象不能作为 R 参数传入。

### 10.2 尚未移植

- `histplot()`、`lineplot()`、`ridgeplot()`；
- `rocplot()`、`forestplot()`；
- survival 和 cumulative incidence；
- `dotplot()`、`heatmapplot()`、phylo；
- Venn、UpSet、Sankey；
- Python multipanel 的绝对布局系统和模型拟合封装。

这些功能不会用一个外观相似的 geom 冒充。后续会先锁定 R 数据对象、统计契约
和可选后端，再按独立批次实现。

### 10.3 图形底层无法完全等价

- Matplotlib 自动 `best` legend；
- renderer 计算的 tight bounding box；
- 每个字符串独立切换 Unicode fallback 字体；
- PDF Type 42 内部结构；
- MuPDF/Illustrator SVG 后处理；
- Matplotlib 与 ggplot2 的 scale expansion 细节；
- `adjustText` 力导标签布局。

因此兼容目标是数据语义、palette、统计默认值、主要图层、标注和物理尺寸，
不是逐像素截图相同。

## 11. 开发与验证

在仓库根目录验证原 Python 项目：

```sh
make test
make lint
```

验证 R 包：

```sh
Rscript -e 'library(cnsplots); testthat::test_dir("r/tests/testthat")'
R CMD build r
R CMD check --no-manual cnsplots_0.0.0.9000.tar.gz
```

当前验证基线：

- Windows R 4.5.3、ggplot2 4.0.3；
- 全部 testthat 测试通过；
- `R CMD build` 通过；
- `R CMD check --no-manual`：0 ERROR、0 WARNING、0 NOTE；
- 原 Python 基线：357 个 pytest 通过、coverage 100%；
- `make lint`：全部 pre-commit hooks 通过。

函数级帮助可直接查看：

```r
?setup_ggplot
?scatterplot
?savefig
```
