local({
  # 1. Define the target script
  script <- ".renv/activate.R"

  # 2. Function to check and source
  try_source <- function(base_path) {
    target <- file.path(base_path, script)
    if (file.exists(target)) {
      source(target)
      return(TRUE)
    }
    return(FALSE)
  }

  # 3. Check current directory first
  if (try_source(".")) return()

  # 4. Search upwards for the project root
  root <- getwd()
  while (root != dirname(root)) {
    # Move up one level
    root <- dirname(root)

    # If we find .renv/activate.R in a parent, source it!
    if (try_source(root)) {
      # Optional: Print a message so you know it worked
      message(sprintf("* Project root found at: %s", root))
      return()
    }
  }
})
