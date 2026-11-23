(function () {
  const releaseNotesContainers = document.querySelectorAll(".js-release-notes");
  if (!releaseNotesContainers.length) {
    return;
  }

  const markdownRenderer = window.snarkdown;
  const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "long" });
  const pageSize = 100;
  const maxPages = 10;

  function getCacheKey(user, repo) {
    return `release-notes:github:${user}/${repo}`;
  }

  function escapeHtml(value) {
    return value.replace(/[&<>]/g, function (character) {
      if (character === "&") {
        return "&amp;";
      }
      if (character === "<") {
        return "&lt;";
      }
      return "&gt;";
    });
  }

  function isSafeUrl(url) {
    try {
      const parsed = new URL(url, window.location.href);
      return ["http:", "https:", "mailto:"].includes(parsed.protocol);
    } catch (error) {
      return false;
    }
  }

  function isExternalUrl(url) {
    try {
      return new URL(url, window.location.href).origin !== window.location.origin;
    } catch (error) {
      return false;
    }
  }

  function sanitizeRenderedContent(root) {
    for (const link of root.querySelectorAll("a")) {
      const href = link.getAttribute("href");
      if (!href || !isSafeUrl(href)) {
        link.replaceWith(document.createTextNode(link.textContent || ""));
        continue;
      }

      if (isExternalUrl(href)) {
        link.rel = "noreferrer noopener";
        link.target = "_blank";
      }
    }

    for (const image of root.querySelectorAll("img")) {
      image.loading = "lazy";
      image.decoding = "async";
    }
  }

  function readCache(cacheKey) {
    try {
      const cachedValue = sessionStorage.getItem(cacheKey);
      if (!cachedValue) {
        return null;
      }
      const payload = JSON.parse(cachedValue);
      return Array.isArray(payload) ? payload : null;
    } catch (error) {
      return null;
    }
  }

  function writeCache(cacheKey, releases) {
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify(releases));
    } catch (error) {
      return;
    }
  }

  function setStatus(container, message, state) {
    const status = container.querySelector(".js-release-notes-status");
    if (!status) {
      return;
    }
    status.hidden = false;
    status.dataset.state = state;
    status.textContent = message;
  }

  function hideStatus(container) {
    const status = container.querySelector(".js-release-notes-status");
    if (!status) {
      return;
    }
    status.hidden = true;
  }

  function renderMarkdown(body) {
    if (typeof markdownRenderer !== "function") {
      return "<p>Release notes could not be rendered in the browser.</p>";
    }

    const source = typeof body === "string" && body.trim()
      ? body
      : "_No release notes provided._";
    return markdownRenderer(escapeHtml(source));
  }

  function slugify(value, fallback) {
    const slug = String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return slug || fallback;
  }

  function createReleaseArticle(release, index) {
    const article = document.createElement("article");
    article.className = "release-notes-entry";

    const header = document.createElement("div");
    header.className = "release-notes-header";

    const heading = document.createElement("h2");
    heading.className = "release-notes-title";
    heading.id = `release-${slugify(
      release.tag_name || release.name,
      `entry-${index}`,
    )}`;
    article.setAttribute("aria-labelledby", heading.id);

    const titleLink = document.createElement("a");
    titleLink.href = release.html_url;
    titleLink.textContent = release.name && release.name !== release.tag_name
      ? release.name
      : release.tag_name;
    titleLink.rel = "noreferrer noopener";
    titleLink.target = "_blank";
    heading.appendChild(titleLink);

    const meta = document.createElement("div");
    meta.className = "release-notes-meta";

    const tag = document.createElement("span");
    tag.className = "release-notes-tag";
    tag.textContent = release.tag_name;
    meta.appendChild(tag);

    const publishedDate = release.published_at || release.created_at;
    if (publishedDate) {
      const date = document.createElement("span");
      date.textContent = dateFormatter.format(new Date(publishedDate));
      meta.appendChild(date);
    }

    const githubLink = document.createElement("a");
    githubLink.className = "release-notes-github-link";
    githubLink.href = release.html_url;
    githubLink.textContent = "View on GitHub";
    githubLink.rel = "noreferrer noopener";
    githubLink.target = "_blank";
    meta.appendChild(githubLink);

    header.appendChild(heading);
    header.appendChild(meta);

    const body = document.createElement("div");
    body.className = "release-notes-body";
    body.innerHTML = renderMarkdown(release.body);
    sanitizeRenderedContent(body);

    article.appendChild(header);
    article.appendChild(body);

    return article;
  }

  function renderReleases(container, releases) {
    const list = container.querySelector(".js-release-notes-list");
    if (!list) {
      return;
    }

    list.replaceChildren();

    if (!releases.length) {
      list.hidden = true;
      setStatus(
        container,
        "No published stable releases are available yet. Browse GitHub Releases for upcoming drafts.",
        "empty",
      );
      return;
    }

    releases.forEach(function (release, index) {
      list.appendChild(createReleaseArticle(release, index));
    });

    list.hidden = false;
    hideStatus(container);
  }

  async function fetchAllReleases(user, repo) {
    const releases = [];

    for (let page = 1; page <= maxPages; page += 1) {
      const response = await fetch(
        `https://api.github.com/repos/${encodeURIComponent(user)}/${encodeURIComponent(repo)}/releases?per_page=${pageSize}&page=${page}`,
        {
          headers: {
            Accept: "application/vnd.github+json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`GitHub API returned ${response.status}`);
      }

      const payload = await response.json();
      if (!Array.isArray(payload)) {
        throw new Error("GitHub API returned an unexpected response");
      }

      releases.push(...payload);

      if (payload.length < pageSize) {
        break;
      }
    }

    return releases.filter(function (release) {
      return !release?.draft && !release?.prerelease;
    });
  }

  async function initReleaseNotes(container) {
    const user = container.dataset.user;
    const repo = container.dataset.repo;
    if (!user || !repo) {
      setStatus(
        container,
        "Release notes are not configured for this page yet.",
        "error",
      );
      return;
    }

    if (typeof markdownRenderer !== "function") {
      setStatus(
        container,
        "Release notes could not be rendered in the browser. Please use GitHub Releases instead.",
        "error",
      );
      return;
    }

    const cacheKey = getCacheKey(user, repo);
    const cachedReleases = readCache(cacheKey);
    if (cachedReleases) {
      renderReleases(container, cachedReleases);
      return;
    }

    setStatus(container, "Loading published releases from GitHub...", "loading");

    try {
      const releases = await fetchAllReleases(user, repo);
      writeCache(cacheKey, releases);
      renderReleases(container, releases);
    } catch (error) {
      setStatus(
        container,
        "Release notes are temporarily unavailable here. Please use GitHub Releases for the latest details.",
        "error",
      );
    }
  }

  releaseNotesContainers.forEach(function (container) {
    void initReleaseNotes(container);
  });
})();
