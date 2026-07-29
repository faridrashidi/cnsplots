with_default_settings <- function(code) {
  previous <- reset_settings()
  on.exit(settings(.list = previous), add = TRUE)
  force(code)
}

test_that("settings expose the Python-compatible visual defaults", {
  with_default_settings({
    current <- settings()

    expect_length(current, 78)
    expect_equal(current$palette_qual, "Ecotyper1")
    expect_equal(current$palette_seq, "gnuplot")
    expect_equal(current$title_fontsize, 8)
    expect_equal(current$legend_fontsize, 7)
    expect_equal(current$axes_linewidth, 0.5)
    expect_false(current$axes_grid)
    expect_false(current$axes_spines_top)
    expect_false(current$axes_spines_right)
    expect_equal(current$xtick_major_size, 2)
    expect_equal(current$ytick_major_size, 2)
    expect_equal(current$xtick_major_width, 0.6)
    expect_equal(current$ytick_major_width, 0.6)
    expect_true(current$savefig_transparent)
    expect_equal(current$savefig_dpi, 288)
    expect_equal(current$figure_width, 150)
    expect_equal(current$figure_height, 150)
  })
})

test_that("settings can be retrieved singly or in groups", {
  with_default_settings({
    expect_equal(settings("title_fontsize"), 8)
    expect_equal(
      settings("title_fontsize", "legend_fontsize"),
      list(title_fontsize = 8, legend_fontsize = 7)
    )
  })
})

test_that("named updates return the values they replace", {
  with_default_settings({
    previous <- settings(title_fontsize = 10, axes_grid = TRUE)

    expect_equal(previous, list(title_fontsize = 8, axes_grid = FALSE))
    expect_equal(settings("title_fontsize"), 10)
    expect_true(settings("axes_grid"))
  })
})

test_that("scoped settings are restored after success and error", {
  with_default_settings({
    before <- settings()

    value <- with_settings(
      list(title_fontsize = 11, axes_grid = TRUE),
      list(
        title_fontsize = settings("title_fontsize"),
        axes_grid = settings("axes_grid")
      )
    )
    expect_equal(value, list(title_fontsize = 11, axes_grid = TRUE))
    expect_identical(settings(), before)

    expect_error(
      with_settings(list(title_fontsize = 12), stop("deliberate failure")),
      "deliberate failure"
    )
    expect_identical(settings(), before)
  })
})

test_that("reset restores all defaults", {
  with_default_settings({
    settings(title_fontsize = 14, savefig_transparent = FALSE)
    previous <- reset_settings()

    expect_equal(previous$title_fontsize, 14)
    expect_false(previous$savefig_transparent)
    expect_equal(settings("title_fontsize"), 8)
    expect_true(settings("savefig_transparent"))
  })
})

test_that("unknown and invalid settings are rejected", {
  with_default_settings({
    expect_error(settings("does_not_exist"), "Unknown cnsplots setting")
    expect_error(settings(does_not_exist = 1), "Unknown cnsplots setting")
    expect_error(settings(title_fontsize = 0), "greater than zero")
    expect_error(settings(axes_grid = NA), "TRUE or FALSE")
    expect_error(settings(axes_edgecolor = "not-a-colour"), "valid R colour")
    expect_error(settings(.list = list(8)), "fully named list")
    expect_error(with_settings(list(8), NULL), "fully named list")
  })
})
